"""Curated seed corpus of Indian Standards metadata, and corpus (de)serialisation.

Provenance and limits — read before relying on this data:

* Records are compiled from publicly listed BIS catalogue metadata
  (designation, title, edition, supersession) and general engineering
  knowledge. They have NOT been verified against official BIS publications, so
  every record carries ``source.verified = false``.
* Clause texts are short paraphrased summaries written for retrieval and
  explanation. They are not normative text and must not be quoted as such.
* Numeric constraints are the commonly cited limits (e.g. IS 456 Table 5,
  IS 10500 acceptable limits). Where a standard allows relaxations or special
  conditions, the ``condition`` text says so.

The data lives in ``data/seed_corpus.json`` (camelCase, the same shape the
database import/export uses). Replace or extend it through
``backend/scripts/seed_standards.py`` with licensed content when available.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..types import (
    Certification,
    ChecklistItem,
    ClauseConstraint,
    Corpus,
    CorpusClause,
    CorpusRelationship,
    CorpusStandard,
    PriorEdition,
    SourceInfo,
    VersionEvent,
)

SEED_PATH = Path(__file__).parent / "data" / "seed_corpus.json"


def checksum(value: str) -> str:
    """32-bit FNV-1a over UTF-16 code units, identical to the TypeScript implementation."""
    h = 0x811C9DC5
    encoded = value.encode("utf-16-le")
    for i in range(0, len(encoded), 2):
        h ^= encoded[i] | (encoded[i + 1] << 8)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def _js_json(value: Any) -> str:
    """``JSON.stringify`` for the corpus payload (compact, key order preserved, integral floats as ints)."""

    def norm(v: Any) -> Any:
        if isinstance(v, float) and v.is_integer():
            return int(v)
        if isinstance(v, dict):
            return {k: norm(x) for k, x in v.items()}
        if isinstance(v, list):
            return [norm(x) for x in v]
        return v

    return json.dumps(norm(value), separators=(",", ":"), ensure_ascii=False)


def constraint_from_dict(d: dict[str, Any]) -> ClauseConstraint:
    return ClauseConstraint(
        parameter=d["parameter"],
        dimension=d["dimension"],
        unit=d["unit"],
        min=d.get("min"),
        max=d.get("max"),
        condition=d["condition"],
        qualifier=d.get("qualifier"),
    )


def checklist_from_dict(d: dict[str, Any]) -> ChecklistItem:
    return ChecklistItem(
        parameter=d["parameter"],
        label=d["label"],
        rationale=d["rationale"],
        clause_id=d["clauseId"],
        severity=d["severity"],
        repair_template=d["repairTemplate"],
    )


def standard_from_dict(d: dict[str, Any], clauses: list[dict[str, Any]] | None = None) -> CorpusStandard:
    cert = d["certification"]
    src = d["source"]
    return CorpusStandard(
        id=d["id"],
        designation=d["designation"],
        year=int(d["year"]),
        number=d["number"],
        title=d["title"],
        scope=d["scope"],
        category=d["category"],
        kind=d["kind"],
        status=d["status"],
        aliases=list(d.get("aliases") or []),
        keywords=list(d.get("keywords") or []),
        certification=Certification(cert.get("scheme"), list(cert.get("bodies") or []), cert.get("relevance", "Low")),
        checklist=[checklist_from_dict(c) for c in d.get("checklist") or []],
        clauses=[
            CorpusClause(
                id=c["id"],
                standard_id=c.get("standardId", d["id"]),
                ref=c.get("ref"),
                heading=c["heading"],
                text=c["text"],
                constraints=[constraint_from_dict(k) for k in c.get("constraints") or []],
            )
            for c in (clauses if clauses is not None else d.get("clauses") or [])
        ],
        source=SourceInfo(src["kind"], bool(src["verified"]), src["note"]),
    )


def relationship_from_dict(d: dict[str, Any]) -> CorpusRelationship:
    return CorpusRelationship(
        id=d["id"],
        type=d["type"],
        from_id=d["fromId"],
        to_id=d["toId"],
        clause_id=d.get("clauseId"),
        confidence=float(d["confidence"]),
        method=d["method"],
        note=d["note"],
    )


def event_from_dict(d: dict[str, Any]) -> VersionEvent:
    return VersionEvent(
        id=d["id"],
        standard_id=d["standardId"],
        date=d.get("date"),
        kind=d["kind"],
        summary=d["summary"],
        severity=d["severity"],
        replaced_by_id=d.get("replacedById"),
    )


def corpus_from_payload(payload: dict[str, Any], version: str | None = None) -> Corpus:
    """Build a Corpus from the camelCase JSON payload; the version defaults to its checksum."""
    if version is None:
        body = _js_json(
            [payload["standards"], payload["relationships"], payload["events"], payload["priorEditions"]]
        )
        version = f"seed-{checksum(body)}"
    return Corpus(
        version=version,
        standards=[standard_from_dict(s) for s in payload["standards"]],
        relationships=[relationship_from_dict(r) for r in payload["relationships"]],
        events=[event_from_dict(e) for e in payload["events"]],
        prior_editions=[
            PriorEdition(p["designation"], int(p["year"]), p["replacedById"]) for p in payload["priorEditions"]
        ],
    )


@lru_cache(maxsize=1)
def seed_corpus() -> Corpus:
    return corpus_from_payload(json.loads(SEED_PATH.read_text(encoding="utf-8")))
