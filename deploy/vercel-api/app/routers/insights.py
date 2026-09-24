"""Engine transparency: configuration, dependency DAG, evaluation results, corpus import.

* ``GET  /api/engine``                       pipeline version and active preset
* ``GET  /api/dependency-dag``               the normative dependency DAG (layers, reduced edges, stats)
* ``GET  /api/standards/{id}/dependencies``  what a standard obliges (closure) and who depends on it (ancestors)
* ``GET  /api/evaluation/runs``              versioned evaluation runs (headline metrics)
* ``GET  /api/evaluation/runs/{run_id}``     one run record with every task, metric and CI
* ``GET  /api/evaluation/classifiers``       the latest classifier comparison
* ``POST /api/admin/corpus/import``          replace the stored corpus with an uploaded JSON payload
"""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from standardos_aiml.pipeline import get_engine
from standardos_aiml.standards.seed import corpus_from_payload

from .. import models as m
from ..config import get_settings
from ..corpus import get_corpus, import_corpus
from ..db import get_db
from ..deps import require_user_id
from ..engine import engine_info
from ..errors import AppError, NotFound

router = APIRouter(prefix="/api", tags=["insights"])

RESULTS = Path(os.environ.get("STANDARDOS_RESULTS_DIR", Path(__file__).resolve().parents[3] / "aiml" / "results"))
RUN_ID = re.compile(r"^[\w.+-]{1,120}$")
HEADLINE = ["id_f1", "cls_macro_f1", "attr_f1", "map_accuracy", "fnd_precision", "fnd_recall", "fnd_f1"]


@router.get("/engine")
def engine():
    return engine_info()


@router.get("/dependency-dag")
def dependency_dag():
    loaded = get_corpus()
    dag = get_engine(loaded.corpus).dag
    return {"corpusVersion": loaded.corpus.version, **dag.to_dict(), "stats": dag.stats()}


@router.get("/standards/{standard_id}/dependencies")
def standard_dependencies(standard_id: str):
    corpus = get_corpus().corpus
    if not corpus.standard(standard_id):
        raise NotFound("Standard not found.")
    dag = get_engine(corpus).dag

    def label(i: str) -> dict[str, str]:
        s = corpus.standard(i)
        return {"id": i, "number": s.number if s else i, "title": s.title if s else ""}

    canon = dag.canon(standard_id)
    return {
        "standard": label(standard_id),
        "canonical": label(canon) if canon != standard_id else None,
        "layer": dag.layer.get(canon, 0),
        "dependsOn": [
            {**label(t), "depth": r.depth, "via": [label(e.source)["number"] for e in r.path[1:]], "type": r.first_type}
            for t, r in sorted(dag.closure(standard_id).items(), key=lambda kv: kv[1].depth)
        ],
        "requiredBy": [label(a) for a in sorted(dag.ancestors(standard_id))],
    }


def _runs() -> list[Path]:
    root = RESULTS / "runs"
    return sorted((p for p in root.glob("*/record.json")), reverse=True) if root.exists() else []


def _headline(record: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for t in record["tasks"]:
        if t["task"] != "documents" or t["variant"] != "txt":
            continue
        out.append(
            {
                "dataset": t["dataset"], "split": t["split"], "role": t["role"], "n": t["n"],
                "metrics": {k: t["metrics"][k] for k in HEADLINE if k in t["metrics"]},
                "ci": {k: t.get("ci", {}).get(k) for k in HEADLINE if k in t.get("ci", {})},
            }
        )
    return out


@router.get("/evaluation/runs")
def evaluation_runs():
    runs = []
    for path in _runs():
        rec = json.loads(path.read_text(encoding="utf-8"))
        runs.append(
            {
                "runId": rec["run_id"], "label": rec.get("label", ""), "createdAt": rec["created_at"],
                "pipelineVersion": rec["pipeline_version"], "config": rec["config"]["name"],
                "gitCommit": rec.get("git_commit"), "blindScored": rec.get("blind_scored", []),
                "documents": _headline(rec),
            }
        )
    return runs


@router.get("/evaluation/runs/{run_id}")
def evaluation_run(run_id: str):
    path = RESULTS / "runs" / run_id / "record.json"
    if not RUN_ID.match(run_id) or not path.exists():
        raise NotFound("Evaluation run not found.")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/evaluation/classifiers")
def classifier_comparison():
    root = RESULTS / "classifiers"
    records = sorted(root.glob("*/record.json"), reverse=True) if root.exists() else []
    if not records:
        raise NotFound("No classifier comparison has been run yet.")
    return json.loads(records[0].read_text(encoding="utf-8"))


def _require_admin(db: Session, user_id: uuid.UUID) -> None:
    user = db.scalar(select(m.User).where(m.User.id == user_id))
    if not user or user.email.lower() not in get_settings().admin_email_list:
        raise AppError("Only corpus administrators (ADMIN_EMAILS) can import standards.", 403)


@router.post("/admin/corpus/import")
async def import_standards(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Import a corpus JSON file (the format of ``aiml/standardos_aiml/standards/data``: standards,
    relationships, events, priorEditions). The upload replaces the active corpus atomically."""
    _require_admin(db, user_id)
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise AppError("Corpus files are limited to 20 MB.", 413)
    try:
        payload = json.loads(raw.decode("utf-8"))
        version = str(payload.get("version") or f"upload-{uuid.uuid4().hex[:8]}")
        corpus = corpus_from_payload(payload, version=version)
    except Exception as exc:
        raise AppError(f"Not a valid corpus file: {exc}") from exc
    if not corpus.standards:
        raise AppError("The corpus file contains no standards.")
    unknown = {r.from_id for r in corpus.relationships} | {r.to_id for r in corpus.relationships}
    unknown -= {s.id for s in corpus.standards}
    if unknown:
        raise AppError(f"Relationships refer to unknown standards: {', '.join(sorted(unknown)[:5])}")
    import_corpus(db, corpus, source=f"upload:{file.filename or 'corpus.json'}")
    return {
        "version": corpus.version,
        "standards": len(corpus.standards),
        "clauses": sum(len(s.clauses) for s in corpus.standards),
        "relationships": len(corpus.relationships),
    }
