"""Analysis API.

Upload → POST /api/analyses (stores the document, queues a run and executes it
in a background task) while the client polls GET /api/runs/{id} for stage
progress → GET /api/documents/{id} for results.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from standardos_aiml.ingest.parse import MAX_UPLOAD_BYTES, ParseError
from standardos_aiml.pipeline import run_pipeline

from ..config import get_settings
from ..corpus import get_corpus
from ..db import get_db
from ..deps import organization_of, require_user_id
from ..errors import AppError, NotFound
from ..report import build_compliance_report, report_filename
from ..samples import sample_workspace
from ..schemas import DocumentPatch
from ..store import (
    audit_trail,
    create_document_with_run,
    delete_document,
    execute_run,
    get_run_status,
    load_snapshots,
    queue_rerun,
    update_document,
)
from ..view import build_document_analysis, snapshot_from_result, summary_of
from .. import doctypes
from ..engine import pipeline_config

router = APIRouter(prefix="/api", tags=["analysis"])

ACCEPTED = re.compile(r"\.(pdf|docx|txt)$", re.I)


@dataclass
class Upload:
    data: Optional[bytes]
    filename: Optional[str]
    mime_type: Optional[str]
    text: Optional[str]
    name: Optional[str]
    document_type: str = "specification"
    document_type_label: Optional[str] = None

    @property
    def extension(self) -> Optional[str]:
        return self.filename.rsplit(".", 1)[-1].lower() if self.filename and "." in self.filename else None

    def title(self) -> str:
        if self.name:
            return self.name
        if self.filename:
            return re.sub(r"[_-]+", " ", re.sub(r"\.[^.]+$", "", self.filename)).strip() or "Uploaded specification"
        first = next((ln.strip() for ln in (self.text or "").split("\n") if len(ln.strip()) > 3), "Pasted specification")
        return f"{first[:87]}…" if len(first) > 90 else first


async def read_upload(
    file: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
    name: Optional[str] = Form(default=None),
    document_type: Optional[str] = Form(default=None, alias="documentType"),
    document_type_label: Optional[str] = Form(default=None, alias="documentTypeLabel"),
) -> Upload:
    data = await file.read(MAX_UPLOAD_BYTES + 1) if file is not None else None
    upload = Upload(
        data=data if data else None,
        filename=file.filename if file is not None and data else None,
        mime_type=(file.content_type or None) if file is not None and data else None,
        text=text if text and text.strip() else None,
        name=name.strip()[:200] if name and name.strip() else None,
    )
    upload.document_type, upload.document_type_label = doctypes.validate(document_type, document_type_label)
    if not upload.data and not upload.text:
        raise AppError("Add a file or paste specification text before analysis.")
    if upload.data is not None and not ACCEPTED.search(upload.filename or ""):
        raise AppError("Unsupported file. Upload PDF, DOCX, or TXT.")
    if upload.data is not None and len(upload.data) > MAX_UPLOAD_BYTES:
        raise AppError("Upload failed. The maximum file size is 20 MB.")
    limit = get_settings().max_text_chars
    if upload.text and len(upload.text) > limit:
        raise AppError(f"Pasted text is limited to {limit:,} characters.")
    return upload


@router.post("/analyses")
def create_analysis(
    background: BackgroundTasks,
    upload: Upload = Depends(read_upload),
    user_id: uuid.UUID = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    data = upload.data if upload.data is not None else (upload.text or "").encode("utf-8")
    document_id, run_id = create_document_with_run(
        db,
        owner_id=user_id,
        organization=organization_of(db, user_id),
        name=upload.title(),
        source_format=(upload.extension or "txt") if upload.data is not None else "text",
        filename=upload.filename,
        mime_type=upload.mime_type,
        data=data,
        document_type=upload.document_type,
        document_type_label=upload.document_type_label,
    )
    if not get_settings().is_serverless:
        background.add_task(execute_run, run_id, user_id)
    return {"documentId": str(document_id), "runId": str(run_id)}


@router.post("/runs/{run_id}/execute")
def execute(run_id: uuid.UUID, user_id: uuid.UUID = Depends(require_user_id)):
    """Execute a queued run synchronously (idempotent; returns the current status if already claimed)."""
    return {"status": execute_run(run_id, user_id)}


@router.get("/runs/{run_id}")
def run_status(run_id: uuid.UUID, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)):
    return get_run_status(db, run_id, user_id)


@router.post("/documents/{document_id}/reanalyze")
def reanalyze(
    document_id: uuid.UUID,
    background: BackgroundTasks,
    user_id: uuid.UUID = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    run_id = queue_rerun(db, document_id, user_id)
    if not get_settings().is_serverless:
        background.add_task(execute_run, run_id, user_id)
    return {"runId": str(run_id)}


@router.get("/documents")
def list_documents(
    summary: bool = False, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)
):
    """Full analyses for the workspace (documents list, compliance, change impact); ``?summary=true`` drops detail."""
    corpus = get_corpus().corpus
    docs = [build_document_analysis(s, corpus) for s in load_snapshots(db, user_id)]
    return [summary_of(d) for d in docs] if summary else docs


@router.get("/documents/{document_id}")
def get_document(document_id: uuid.UUID, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)):
    snapshots = load_snapshots(db, user_id, document_id)
    if not snapshots:
        raise NotFound("Document not found.")
    return build_document_analysis(snapshots[0], get_corpus().corpus)


@router.get("/document-types")
def document_types():
    return doctypes.catalogue()


@router.patch("/documents/{document_id}")
def patch_document(
    document_id: uuid.UUID,
    body: DocumentPatch,
    background: BackgroundTasks,
    user_id: uuid.UUID = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Rename or re-type a document; a type change that alters analysis queues a new run."""
    run_id = update_document(
        db, document_id, user_id,
        name=body.name, document_type=body.document_type, document_type_label=body.document_type_label,
    )
    if run_id and not get_settings().is_serverless:
        background.add_task(execute_run, run_id, user_id)
    return {"runId": str(run_id) if run_id else None}


@router.delete("/documents/{document_id}")
def remove_document(document_id: uuid.UUID, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)):
    delete_document(db, document_id, user_id)
    return {"deleted": True}


@router.get("/documents/{document_id}/audit")
def get_audit(document_id: uuid.UUID, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)):
    return audit_trail(db, document_id, user_id)


@router.get("/documents/{document_id}/report")
def get_report(document_id: uuid.UUID, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)):
    snapshots = load_snapshots(db, user_id, document_id)
    if not snapshots:
        raise NotFound("Document not found.")
    doc = build_document_analysis(snapshots[0], get_corpus().corpus)
    return {"filename": report_filename(doc), "markdown": build_compliance_report(doc)}


# ---------------------------------------------------------------------------
# Demo workspace (no account): real pipeline, nothing persisted.
# ---------------------------------------------------------------------------


@router.get("/samples")
def samples():
    return sample_workspace()


@router.post("/analyze/stateless")
def analyze_stateless(upload: Upload = Depends(read_upload)):
    loaded = get_corpus()
    source = (upload.data, upload.filename or "document.txt") if upload.data is not None else (upload.text or "")
    try:
        result = run_pipeline(source, loaded.corpus, config=doctypes.config_for(pipeline_config(), upload.document_type))
    except ParseError as exc:
        raise AppError(exc.message) from exc
    return build_document_analysis(
        snapshot_from_result(
            result,
            documentId=f"local-{uuid.uuid4()}",
            name=upload.title(),
            organization="Demo workspace",
            type=(upload.extension or "txt").upper() if upload.data is not None else "Text",
            documentType=upload.document_type,
            documentTypeLabel=doctypes.display_label(upload.document_type, upload.document_type_label),
            analyzedAt=datetime.now(timezone.utc).isoformat(),
            isSample=False,
            corpusSource=loaded.source,
        ),
        loaded.corpus,
    )
