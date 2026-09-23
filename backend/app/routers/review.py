"""Findings, gaps, conflicts, evidence, review and repair decisions.

AI proposes → a human reviews → the decision is recorded in audit_events with
before/after state and the provenance of what was decided.
"""

from __future__ import annotations

import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..corpus import get_corpus
from ..db import get_db
from ..deps import require_user_id
from ..errors import NotFound
from ..schemas import RepairDecision, ReviewBody
from ..store import decide_repair, load_snapshots, review_finding
from ..view import build_document_analysis

router = APIRouter(prefix="/api", tags=["review"])


@router.get("/findings")
def list_findings(
    kind: Optional[Literal["verified", "missing", "conflicting", "outdated", "certification"]] = None,
    severity: Optional[Literal["low", "medium", "high"]] = None,
    reviewStatus: Optional[Literal["open", "confirmed", "dismissed"]] = None,  # noqa: N803 — wire name
    documentId: Optional[uuid.UUID] = None,  # noqa: N803
    user_id: uuid.UUID = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """``kind=missing`` is the gap API, ``kind=conflicting`` the conflict API."""
    corpus = get_corpus().corpus
    findings = [f for s in load_snapshots(db, user_id, documentId) for f in build_document_analysis(s, corpus)["findings"]]
    return [
        f
        for f in findings
        if (not kind or f["status"] == kind)
        and (not severity or f["severity"] == severity)
        and (not reviewStatus or f["reviewStatus"] == reviewStatus)
    ]


@router.get("/findings/{finding_id}")
def get_finding(finding_id: uuid.UUID, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)):
    """Evidence API: one finding with its evidence and provenance."""
    corpus = get_corpus().corpus
    for s in load_snapshots(db, user_id):
        for f in build_document_analysis(s, corpus)["findings"]:
            if f["id"] == str(finding_id):
                return f
    raise NotFound("Finding not found.")


@router.post("/findings/{finding_id}/review")
def review(
    finding_id: uuid.UUID, body: ReviewBody, user_id: uuid.UUID = Depends(require_user_id), db: Session = Depends(get_db)
):
    review_finding(db, finding_id, user_id, body.status, body.note or None)
    return {"ok": True}


@router.post("/repairs/{repair_id}/decision")
def repair_decision(
    repair_id: uuid.UUID,
    body: RepairDecision,
    user_id: uuid.UUID = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    return decide_repair(db, repair_id, user_id, body.decision, body.text)
