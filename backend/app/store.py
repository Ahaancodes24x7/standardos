"""Persistence and orchestration for analysis runs.

Job model: an upload creates a document and a queued run, and the API
schedules execution in a background task while the client polls the run row
for stage progress. Execution claims the run atomically (queued → running), so
a duplicate call or the cron sweeper cannot run it twice. A run whose heartbeat
stops (crash, restart) is re-queued by the sweeper up to MAX_ATTEMPTS times.
This keeps the job queue in Postgres, which the app already depends on, with no
separate broker.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session
from standardos_aiml.ingest.parse import ParseError, decode_text
from standardos_aiml.llm_repair import REPAIR_MODEL, llm_repair_enabled, polish_repairs
from standardos_aiml.pipeline import run_pipeline
from standardos_aiml.serialize import to_wire
from standardos_aiml.types import AnalysisResult

from . import models as m
from .corpus import get_corpus
from .db import session_scope
from .errors import AppError, NotFound
from .engine import pipeline_config

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
STALE_AFTER = timedelta(minutes=10)
FORMAT_LABEL = {"pdf": "PDF", "docx": "DOCX", "txt": "TXT", "text": "Text"}


def now() -> datetime:
    return datetime.now(timezone.utc)


def audit(
    db: Session,
    *,
    actor_id: Optional[uuid.UUID],
    document_id: Optional[uuid.UUID],
    entity_type: str,
    entity_id: str,
    action: str,
    before: Any = None,
    after: Any = None,
) -> None:
    db.add(
        m.AuditEvent(
            actor_id=actor_id,
            document_id=document_id,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            before=before,
            after=after,
        )
    )


# ---------------------------------------------------------------------------
# Create / execute
# ---------------------------------------------------------------------------


def create_document_with_run(
    db: Session,
    *,
    owner_id: uuid.UUID,
    organization: str,
    name: str,
    source_format: str,
    filename: Optional[str],
    mime_type: Optional[str],
    data: bytes,
) -> tuple[uuid.UUID, uuid.UUID]:
    sha256 = hashlib.sha256(data).hexdigest()
    doc = m.Document(
        owner_id=owner_id,
        name=name,
        organization=organization,
        source_format=source_format,
        filename=filename,
        mime_type=mime_type,
        byte_size=len(data),
        sha256=sha256,
        original=data,
    )
    db.add(doc)
    db.flush()
    run = m.AnalysisRun(document_id=doc.id, owner_id=owner_id)
    db.add(run)
    db.flush()
    audit(db, actor_id=owner_id, document_id=doc.id, entity_type="document", entity_id=str(doc.id),
          action="uploaded", after={"name": name, "sha256": sha256, "byteSize": len(data)})
    audit(db, actor_id=owner_id, document_id=doc.id, entity_type="run", entity_id=str(run.id), action="queued")
    db.commit()
    return doc.id, run.id


def queue_rerun(db: Session, document_id: uuid.UUID, owner_id: uuid.UUID) -> uuid.UUID:
    doc = db.scalar(select(m.Document).where(m.Document.id == document_id, m.Document.owner_id == owner_id))
    if not doc:
        raise NotFound("Document not found.")
    run = m.AnalysisRun(document_id=document_id, owner_id=owner_id)
    db.add(run)
    db.flush()
    audit(db, actor_id=owner_id, document_id=document_id, entity_type="run", entity_id=str(run.id),
          action="queued", after={"reason": "re-analysis requested"})
    db.commit()
    return run.id


def _claim_run(db: Session, run_id: uuid.UUID) -> bool:
    """Atomically move a queued run to running. Returns False if another worker has it."""
    claimed = db.execute(
        update(m.AnalysisRun)
        .where(m.AnalysisRun.id == run_id, m.AnalysisRun.status == "queued")
        .values(
            status="running",
            attempts=m.AnalysisRun.attempts + 1,
            started_at=now(),
            heartbeat_at=now(),
            stage=0,
            error=None,
            error_code=None,
        )
        .returning(m.AnalysisRun.id)
    ).all()
    db.commit()
    return len(claimed) == 1


def execute_run(run_id: uuid.UUID, owner_id: Optional[uuid.UUID]) -> str:
    """Run the pipeline for a queued run and persist the result. Returns the final status."""
    with session_scope() as db:
        run = db.get(m.AnalysisRun, run_id)
        if not run or (owner_id and run.owner_id != owner_id):
            raise NotFound("Analysis not found.")
        document_id = run.document_id
        if not _claim_run(db, run_id):
            db.refresh(run)
            return run.status
        doc = db.get(m.Document, document_id)
        started = time.perf_counter()
        try:
            if not doc or doc.original is None:
                raise RuntimeError("The stored document could not be read.")
            loaded = get_corpus()
            source = (
                decode_text(bytes(doc.original))
                if doc.source_format == "text"
                else (bytes(doc.original), doc.filename or f"document.{doc.source_format}")
            )

            def on_stage(name: str, index: int) -> None:
                db.execute(
                    update(m.AnalysisRun)
                    .where(m.AnalysisRun.id == run_id)
                    .values(stage=index, stage_name=name, heartbeat_at=now())
                )
                db.commit()

            result = run_pipeline(source, loaded.corpus, on_stage=on_stage, config=pipeline_config())
            result.repairs = polish_repairs(result.repairs)
            _persist_result(db, run_id, document_id, result, loaded.source)
            audit(db, actor_id=owner_id, document_id=document_id, entity_type="run", entity_id=str(run_id),
                  action="succeeded",
                  after={"findings": len(result.findings), "readiness": result.readiness.score,
                         "ms": round((time.perf_counter() - started) * 1000)})
            db.commit()
            return "succeeded"
        except Exception as error:  # noqa: BLE001 — any failure is recorded on the run
            db.rollback()
            if isinstance(error, ParseError):
                code, message = error.code, error.message
            else:
                code = "internal"
                message = "The analysis failed unexpectedly. Your document is stored; please retry."
                log.exception("[analysis] run %s failed", run_id)
            db.execute(
                update(m.AnalysisRun)
                .where(m.AnalysisRun.id == run_id)
                .values(status="failed", error=message, error_code=code, finished_at=now())
            )
            audit(db, actor_id=owner_id, document_id=document_id, entity_type="run", entity_id=str(run_id),
                  action="failed", after={"code": code, "message": message})
            db.commit()
            return "failed"


def _persist_result(
    db: Session, run_id: uuid.UUID, document_id: uuid.UUID, result: AnalysisResult, corpus_source: str
) -> None:
    # Idempotent on retry: clear anything a previous attempt wrote.
    db.execute(delete(m.Requirement).where(m.Requirement.run_id == run_id))
    db.execute(delete(m.Finding).where(m.Finding.run_id == run_id))

    req_ids: dict[str, uuid.UUID] = {}
    for r in result.requirements:
        w = to_wire(r)
        row = m.Requirement(
            run_id=run_id,
            local_id=r.id,
            text=r.text,
            span_start=r.span.start,
            span_end=r.span.end,
            page=r.page,
            section_label=r.section_label,
            modality=r.modality,
            category=r.category,
            category_scores=w["categoryScores"],
            attributes=w["attributes"],
            quantities=w["quantities"],
            references=w["references"],
            entities=w["entities"],
            terms=r.terms,
            vague=r.vague,
            provenance=w["provenance"],
        )
        db.add(row)
        db.flush()
        req_ids[r.id] = row.id

    for mapping in result.mappings:
        rid = req_ids.get(mapping.requirement_id)
        if not rid:
            continue
        for rank, h in enumerate(mapping.hits):
            db.add(
                m.RequirementStandardLink(
                    run_id=run_id,
                    requirement_id=rid,
                    standard_id=h.standard_id,
                    clause_id=h.clause_id,
                    rank=rank,
                    score=h.score,
                    confidence=h.confidence,
                    basis=mapping.basis if rank == 0 else "retrieval",
                    explanation=h.explanation,
                    provenance=to_wire(h.provenance),
                )
            )

    finding_ids: dict[str, uuid.UUID] = {}
    for f in result.findings:
        row = m.Finding(
            run_id=run_id,
            document_id=document_id,
            local_id=f.id,
            kind=f.kind,
            rule=f.rule,
            parameter=f.parameter,
            title=f.title,
            severity=f.severity,
            requirement_local_id=f.requirement_id,
            requirement_text=f.requirement_text,
            standard_id=f.standard_id,
            clause_id=f.clause_id,
            standard_label=f.standard_label,
            reason=f.reason,
            action=f.action,
            provenance=to_wire(f.provenance),
        )
        db.add(row)
        db.flush()
        finding_ids[f.id] = row.id
        for ordinal, e in enumerate(f.evidence):
            db.add(
                m.EvidenceRow(
                    finding_id=row.id,
                    ordinal=ordinal,
                    kind=e.kind,
                    label=e.label,
                    excerpt=e.excerpt,
                    requirement_local_id=e.requirement_id,
                    span_start=e.span.start if e.span else None,
                    span_end=e.span.end if e.span else None,
                    standard_id=e.standard_id,
                    clause_id=e.clause_id,
                    relationship_ids=e.relationship_ids,
                )
            )

    for r in result.repairs:
        fid = finding_ids.get(r.finding_id)
        if not fid:
            continue
        db.add(
            m.Repair(
                run_id=run_id,
                finding_id=fid,
                local_id=r.id,
                original=r.original,
                recommended=r.recommended,
                evidence_label=r.evidence_label,
                reason=r.reason,
                provenance=to_wire(r.provenance),
            )
        )

    db.execute(
        update(m.AnalysisRun)
        .where(m.AnalysisRun.id == run_id)
        .values(
            status="succeeded",
            stage=8,
            stage_name="reporting",
            finished_at=now(),
            pipeline_version=result.pipeline_version,
            corpus_version=f"{result.corpus_version} ({corpus_source})",
            llm_model=REPAIR_MODEL if llm_repair_enabled() else None,
            parser=result.document.parser,
            page_count=len(result.document.pages),
            extracted_text=result.document.text,
            warnings=result.document.warnings,
            readiness=result.readiness.score,
            readiness_detail={"formula": result.readiness.formula, "inputs": result.readiness.inputs},
            applicable_standard_ids=result.applicable_standard_ids,
            graph=to_wire(result.graph),
            timings=result.timings_ms,
        )
    )


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------


def get_run_status(db: Session, run_id: uuid.UUID, owner_id: uuid.UUID) -> dict[str, Any]:
    run = db.scalar(select(m.AnalysisRun).where(m.AnalysisRun.id == run_id, m.AnalysisRun.owner_id == owner_id))
    if not run:
        raise NotFound("Analysis not found.")
    return {
        "runId": str(run.id),
        "documentId": str(run.document_id),
        "status": run.status,
        "stage": run.stage,
        "stageName": run.stage_name,
        "error": run.error,
        "errorCode": run.error_code,
    }


def _local_number(local_id: str) -> int:
    digits = re.sub(r"\D", "", local_id)
    return int(digits) if digits else 0


def load_snapshots(db: Session, owner_id: uuid.UUID, document_id: Optional[uuid.UUID] = None) -> list[dict[str, Any]]:
    """Latest run of each of the owner's documents (optionally one document), as view snapshots."""
    query = select(m.Document).where(m.Document.owner_id == owner_id)
    if document_id:
        query = query.where(m.Document.id == document_id)
    docs = db.scalars(query.order_by(m.Document.created_at.desc())).all()
    if not docs:
        return []
    runs = db.scalars(
        select(m.AnalysisRun)
        .where(m.AnalysisRun.document_id.in_([d.id for d in docs]))
        .order_by(m.AnalysisRun.created_at.desc())
    ).all()
    latest: dict[uuid.UUID, m.AnalysisRun] = {}
    for run in runs:
        latest.setdefault(run.document_id, run)
    run_ids = [r.id for r in latest.values()]
    if not run_ids:
        return []

    req_rows = db.scalars(select(m.Requirement).where(m.Requirement.run_id.in_(run_ids))).all()
    link_rows = db.scalars(
        select(m.RequirementStandardLink).where(m.RequirementStandardLink.run_id.in_(run_ids))
    ).all()
    finding_rows = db.scalars(select(m.Finding).where(m.Finding.run_id.in_(run_ids))).all()
    repair_rows = db.scalars(select(m.Repair).where(m.Repair.run_id.in_(run_ids))).all()
    evidence_rows = (
        db.scalars(select(m.EvidenceRow).where(m.EvidenceRow.finding_id.in_([f.id for f in finding_rows]))).all()
        if finding_rows
        else []
    )
    evidence_by_finding: dict[uuid.UUID, list[m.EvidenceRow]] = {}
    for e in evidence_rows:
        evidence_by_finding.setdefault(e.finding_id, []).append(e)
    links_by_req: dict[uuid.UUID, list[m.RequirementStandardLink]] = {}
    for link in link_rows:
        links_by_req.setdefault(link.requirement_id, []).append(link)

    snapshots: list[dict[str, Any]] = []
    for doc in docs:
        run = latest.get(doc.id)
        if not run:
            continue
        reqs = sorted((r for r in req_rows if r.run_id == run.id), key=lambda r: r.span_start)
        requirements = [
            {
                "id": r.local_id,
                "text": r.text,
                "span": {"start": r.span_start, "end": r.span_end},
                "sectionId": None,
                "sectionLabel": r.section_label,
                "page": r.page,
                "modality": r.modality,
                "category": r.category,
                "categoryScores": r.category_scores,
                "quantities": r.quantities,
                "references": r.references,
                "entities": r.entities,
                "attributes": r.attributes,
                "terms": r.terms,
                "vague": r.vague,
                "provenance": r.provenance,
            }
            for r in reqs
        ]
        mappings = []
        for r in reqs:
            rows = sorted(links_by_req.get(r.id, []), key=lambda link: link.rank)
            mappings.append(
                {
                    "requirementId": r.local_id,
                    "hits": [
                        {
                            "standardId": link.standard_id,
                            "clauseId": link.clause_id,
                            "score": link.score,
                            "confidence": link.confidence,
                            "explanation": link.explanation,
                            "provenance": link.provenance,
                        }
                        for link in rows
                    ],
                    "basis": rows[0].basis if rows else "none",
                }
            )
        f_rows = sorted((f for f in finding_rows if f.run_id == run.id), key=lambda f: _local_number(f.local_id))
        finding_local = {f.id: f.local_id for f in f_rows}
        findings = []
        for f in f_rows:
            evidence = []
            for e in sorted(evidence_by_finding.get(f.id, []), key=lambda e: e.ordinal):
                ev: dict[str, Any] = {"kind": e.kind, "label": e.label, "excerpt": e.excerpt}
                if e.requirement_local_id:
                    ev["requirementId"] = e.requirement_local_id
                if e.span_start is not None and e.span_end is not None:
                    ev["span"] = {"start": e.span_start, "end": e.span_end}
                if e.standard_id:
                    ev["standardId"] = e.standard_id
                if e.clause_id:
                    ev["clauseId"] = e.clause_id
                if e.relationship_ids:
                    ev["relationshipIds"] = e.relationship_ids
                evidence.append(ev)
            finding: dict[str, Any] = {
                "id": f.local_id,
                "dbId": str(f.id),
                "kind": f.kind,
                "rule": f.rule,
                "title": f.title,
                "severity": f.severity,
                "requirementId": f.requirement_local_id,
                "requirementText": f.requirement_text,
                "standardId": f.standard_id,
                "clauseId": f.clause_id,
                "standardLabel": f.standard_label,
                "reason": f.reason,
                "action": f.action,
                "evidence": evidence,
                "provenance": f.provenance,
                "reviewStatus": f.review_status,
                "reviewNote": f.review_note,
            }
            if f.parameter:
                finding["parameter"] = f.parameter
            findings.append(finding)
        repairs = [
            {
                "id": r.local_id,
                "dbId": str(r.id),
                "findingId": finding_local.get(r.finding_id, ""),
                "original": r.original,
                "recommended": r.recommended,
                "evidenceLabel": r.evidence_label,
                "reason": r.reason,
                "provenance": r.provenance,
                "status": r.status,
                "finalText": r.final_text,
            }
            for r in sorted((r for r in repair_rows if r.run_id == run.id), key=lambda r: _local_number(r.local_id))
        ]
        source_match = re.search(r"\(([^)]+)\)$", run.corpus_version or "")
        snapshots.append(
            {
                "documentId": str(doc.id),
                "name": doc.name,
                "organization": doc.organization,
                "type": FORMAT_LABEL.get(doc.source_format, doc.source_format.upper()),
                "analyzedAt": (run.finished_at or run.created_at).isoformat(),
                "runId": str(run.id),
                "runStatus": run.status,
                "runError": run.error,
                "pipelineVersion": run.pipeline_version,
                "corpusVersion": re.sub(r"\s*\([^)]+\)$", "", run.corpus_version) if run.corpus_version else None,
                "corpusSource": source_match.group(1) if source_match else None,
                "warnings": run.warnings or [],
                "readiness": run.readiness or 0,
                "readinessFormula": (run.readiness_detail or {}).get("formula"),
                "applicableStandardIds": run.applicable_standard_ids or [],
                "graph": run.graph,
                "requirements": requirements,
                "mappings": mappings,
                "findings": findings,
                "repairs": repairs,
                "isSample": False,
                "persisted": True,
            }
        )
    return snapshots


# ---------------------------------------------------------------------------
# Human review
# ---------------------------------------------------------------------------


def review_finding(db: Session, finding_id: uuid.UUID, owner_id: uuid.UUID, status: str, note: Optional[str]) -> None:
    row = db.execute(
        select(m.Finding, m.Document.owner_id)
        .join(m.Document, m.Document.id == m.Finding.document_id)
        .where(m.Finding.id == finding_id)
    ).first()
    if not row or row[1] != owner_id:
        raise NotFound("Finding not found.")
    finding: m.Finding = row[0]
    before = {"reviewStatus": finding.review_status, "reviewNote": finding.review_note}
    finding.review_status = status
    finding.review_note = note
    finding.reviewed_by = owner_id
    finding.reviewed_at = now()
    audit(db, actor_id=owner_id, document_id=finding.document_id, entity_type="finding", entity_id=str(finding_id),
          action=f"review:{status}", before=before,
          after={"reviewStatus": status, "reviewNote": note, "title": finding.title, "provenance": finding.provenance})
    db.commit()


def decide_repair(
    db: Session, repair_id: uuid.UUID, owner_id: uuid.UUID, decision: str, text: Optional[str]
) -> dict[str, Any]:
    row = db.execute(
        select(m.Repair, m.Finding.document_id, m.Document.owner_id)
        .join(m.Finding, m.Finding.id == m.Repair.finding_id)
        .join(m.Document, m.Document.id == m.Finding.document_id)
        .where(m.Repair.id == repair_id)
    ).first()
    if not row or row[2] != owner_id:
        raise NotFound("Repair not found.")
    repair: m.Repair = row[0]
    if decision == "edited" and not text:
        raise AppError("Edited repairs need the final text.")
    final_text = text if decision == "edited" else repair.recommended if decision == "accepted" else None
    before = {"status": repair.status, "finalText": repair.final_text}
    repair.status = decision
    repair.final_text = final_text
    repair.decided_by = None if decision == "pending" else owner_id
    repair.decided_at = None if decision == "pending" else now()
    audit(db, actor_id=owner_id, document_id=row[1], entity_type="repair", entity_id=str(repair_id),
          action=f"repair:{decision}", before=before,
          after={"status": decision, "finalText": final_text, "recommended": repair.recommended,
                 "provenance": repair.provenance})
    db.commit()
    return {"status": decision, "finalText": final_text}


def _summarise(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    parts = []
    for key in ("title", "name", "reviewStatus", "reviewNote", "status", "finalText", "code", "message", "findings",
                "readiness", "reason"):
        v = value.get(key)
        if v is not None and v != "":
            parts.append(f"{key}: {str(v)[:160]}")
    return " · ".join(parts)


def audit_trail(db: Session, document_id: uuid.UUID, owner_id: uuid.UUID) -> list[dict[str, Any]]:
    doc = db.scalar(select(m.Document).where(m.Document.id == document_id, m.Document.owner_id == owner_id))
    if not doc:
        raise NotFound("Document not found.")
    rows = db.execute(
        select(m.AuditEvent, m.User.email)
        .outerjoin(m.User, m.User.id == m.AuditEvent.actor_id)
        .where(m.AuditEvent.document_id == document_id)
        .order_by(m.AuditEvent.created_at.desc())
    ).all()
    return [
        {
            "id": str(event.id),
            "at": event.created_at.isoformat(),
            "actor": email,
            "entityType": event.entity_type,
            "entityId": event.entity_id,
            "action": event.action,
            "detail": _summarise(event.after),
        }
        for event, email in rows
    ]


# ---------------------------------------------------------------------------
# Sweeper (cron)
# ---------------------------------------------------------------------------


def sweep_runs(limit: int = 3) -> dict[str, Any]:
    """Re-queue stalled runs, fail runs out of attempts, then execute a few queued runs."""
    requeued = failed = 0
    with session_scope() as db:
        stale = db.scalars(
            select(m.AnalysisRun).where(
                m.AnalysisRun.status == "running",
                (m.AnalysisRun.heartbeat_at < now() - STALE_AFTER) | m.AnalysisRun.heartbeat_at.is_(None),
            )
        ).all()
        for run in stale:
            if run.attempts >= MAX_ATTEMPTS:
                run.status = "failed"
                run.error = "The analysis stopped responding and was abandoned after several attempts."
                run.error_code = "stalled"
                run.finished_at = now()
                failed += 1
            else:
                run.status = "queued"
                requeued += 1
        db.commit()
        # Leave very fresh queued runs to the request that created them.
        queued = db.scalars(
            select(m.AnalysisRun.id)
            .where(m.AnalysisRun.status == "queued", m.AnalysisRun.created_at < now() - timedelta(seconds=60))
            .order_by(m.AnalysisRun.created_at)
            .limit(limit)
        ).all()
    executed = []
    for run_id in queued:
        execute_run(run_id, None)
        executed.append(str(run_id))
    return {"requeued": requeued, "failed": failed, "executed": executed}
