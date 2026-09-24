"""Standards knowledge API: catalogue, detail, semantic search, graph queries,
change impact and corpus status. Catalogue, detail, search and graph are
public, since the public /search and /standard pages use them.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from standardos_aiml.nlp.requirements import structure_fragment
from standardos_aiml.pipeline import get_engine
from standardos_aiml.serialize import to_wire
from standardos_aiml.standards.retrieval import RetrievalOptions
from standardos_aiml.types import RELATIONSHIP_TYPES, Corpus, CorpusStandard

from ..corpus import get_corpus
from ..db import get_db
from ..deps import optional_user_id
from ..errors import NotFound, Unauthorized
from ..samples import sample_workspace
from ..schemas import SearchBody
from ..store import load_snapshots
from ..view import build_document_analysis

router = APIRouter(prefix="/api", tags=["standards"])

STATUS_LABEL = {
    "current": "Current",
    "amended": "Amended",
    "reaffirmed": "Reaffirmed",
    "superseded": "Superseded",
    "withdrawn": "Withdrawn",
}
CHANGE_LABEL = {
    "amendment": "Amendment recorded",
    "revision": "Revision published",
    "supersession": "Superseded",
    "withdrawal": "Withdrawn",
    "reaffirmation": "Reaffirmation recorded",
}


def _section(clause: Any) -> str:
    return f"Clause {clause.ref} — {clause.heading}" if clause.ref else clause.heading


def to_standard(corpus: Corpus, s: CorpusStandard) -> dict[str, Any]:
    rels = [r for r in corpus.relationships if s.id in (r.from_id, r.to_id)]
    relationships = []
    for r in rels:
        out = r.from_id == s.id
        other = corpus.standard(r.to_id if out else r.from_id)
        relationships.append(
            {
                "id": r.id,
                "type": r.type,
                "direction": "out" if out else "in",
                "standardId": other.id if other else "",
                "number": other.number if other else "",
                "note": r.note,
                "confidence": r.confidence,
                "method": r.method,
            }
        )
    return {
        "id": s.id,
        "number": s.number,
        "title": s.title,
        "scope": s.scope,
        "category": s.category,
        "language": "English",
        "year": s.year,
        "clauses": [{"id": c.id, "section": _section(c), "text": c.text} for c in s.clauses],
        "relatedStandardIds": list(dict.fromkeys(r.to_id if r.from_id == s.id else r.from_id for r in rels)),
        "certificationBodies": s.certification.bodies,
        "status": STATUS_LABEL[s.status],
        "relationships": relationships,
        "events": [
            {"date": e.date, "kind": e.kind, "summary": e.summary} for e in corpus.events if e.standard_id == s.id
        ],
        "sourceNote": s.source.note,
        "verified": s.source.verified,
    }


@router.get("/standards")
def list_standards():
    corpus = get_corpus().corpus
    out = []
    for s in corpus.standards:
        related_ids = list(
            dict.fromkeys(
                x
                for r in corpus.relationships
                for x in ([r.to_id] if r.from_id == s.id else [r.from_id] if r.to_id == s.id else [])
            )
        )
        out.append(
            {
                "id": s.id,
                "number": s.number,
                "title": s.title,
                "category": s.category,
                "status": STATUS_LABEL[s.status],
                "related": [corpus.standard(i).number for i in related_ids if corpus.standard(i)],
                "certification": s.certification.relevance,
                "verified": s.source.verified,
            }
        )
    return out


@router.get("/standards/{standard_id}")
def get_standard(standard_id: str):
    corpus = get_corpus().corpus
    s = corpus.standard(standard_id)
    if not s:
        raise NotFound("Standard not found.")
    return to_standard(corpus, s)


@router.post("/standards/search")
def search_standards(body: SearchBody):
    corpus = get_corpus().corpus
    index = get_engine(corpus).index
    fragment = structure_fragment(body.query)
    resolved = [r for r in (index.resolver.resolve(ref) for ref in fragment.references) if r.standard_id]
    hits = index.retrieve(
        fragment, resolved, [], RetrievalOptions(expansion=False, document_context=False, rerank=True, min_confidence=0.2, top_k=20)
    )

    def in_year(year: int) -> bool:
        if not body.year_ranges:
            return True
        return any(
            (r == "2020-" and year >= 2020) or (r == "2010-2019" and 2010 <= year <= 2019) or (r == "-2009" and year < 2010)
            for r in body.year_ranges
        )

    def in_domain(category: str) -> bool:
        if not body.domains:
            return True
        return any((d.lower().split(" ")[0] if d else "") in category.lower() for d in body.domains)

    results = []
    for hit in hits:
        s = corpus.standard(hit.standard_id)
        clause = next((c for c in s.clauses if c.id == hit.clause_id), None) if s else None
        if not s or not clause or not in_year(s.year) or not in_domain(s.category):
            continue
        results.append(
            {
                "standard": to_standard(corpus, s),
                "matchedClause": {"id": clause.id, "section": _section(clause), "text": clause.text},
                "confidenceScore": round(hit.confidence * 100),
                "explanation": hit.explanation,
                "provenance": to_wire(hit.provenance),
            }
        )
    return results[: body.limit or 8]


@router.get("/standards/{standard_id}/graph")
def standard_graph(
    standard_id: str,
    depth: int = Query(default=1, ge=1, le=3),
    types: Optional[list[str]] = Query(default=None),
):
    """Graph query: neighbourhood of a standard up to ``depth`` hops, optionally filtered by edge type."""
    corpus = get_corpus().corpus
    allowed = {t for t in types if t in RELATIONSHIP_TYPES} if types else None
    nodes = [standard_id]
    seen = {standard_id}
    edges: dict[str, dict[str, Any]] = {}
    frontier = {standard_id}
    for _ in range(depth):
        nxt: set[str] = set()
        for r in corpus.relationships:
            if allowed is not None and r.type not in allowed:
                continue
            if r.from_id in frontier or r.to_id in frontier:
                edges[r.id] = {
                    "id": r.id, "type": r.type, "from": r.from_id, "to": r.to_id,
                    "confidence": r.confidence, "method": r.method,
                }
                for i in (r.from_id, r.to_id):
                    if i not in seen:
                        seen.add(i)
                        nodes.append(i)
                        nxt.add(i)
        frontier = nxt
    return {
        "nodes": [
            {
                "id": i,
                "number": s.number if (s := corpus.standard(i)) else i,
                "title": s.title if s else "",
                "status": STATUS_LABEL[s.status] if s else "Unknown",
            }
            for i in nodes
        ],
        "edges": list(edges.values()),
    }


def _affects(doc: dict[str, Any], standard_id: str) -> bool:
    return any(r.get("standardId") == standard_id for r in doc["requirements"]) or any(
        any(e.get("standardId") == standard_id for e in (f.get("evidence") or [])) for f in doc["findings"]
    )


def _affected(documents: list[dict[str, Any]], standard_id: str, dag: Any, corpus: Corpus) -> list[dict[str, Any]]:
    """Documents that use the changed standard directly, or through a standard whose normative
    obligations include it (dependency DAG ancestors: IS 269 changes → specs citing IS 456)."""
    out = []
    ancestors = sorted(dag.ancestors(standard_id)) if dag is not None else []
    for d in documents:
        if d["runStatus"] != "succeeded":
            continue
        entry = {"name": d["name"], "documentId": None if d["isSample"] else d["id"]}
        if _affects(d, standard_id):
            out.append(entry)
            continue
        via = next((a for a in ancestors if _affects(d, a)), None)
        if via:
            s = corpus.standard(via)
            out.append({**entry, "via": s.number if s else via})
    return out


@router.get("/change-impact")
def change_impact(
    scope: Literal["workspace", "sample"] = "workspace",
    user_id: Optional[uuid.UUID] = Depends(optional_user_id),
    db: Session = Depends(get_db),
):
    corpus = get_corpus().corpus
    if scope == "sample":
        documents = sample_workspace()
    else:
        if not user_id:
            raise Unauthorized()
        documents = [build_document_analysis(s, corpus) for s in load_snapshots(db, user_id)]
    dag = get_engine(corpus).dag
    events = []
    for e in corpus.events:
        s = corpus.standard(e.standard_id)
        events.append(
            {
                "id": e.id,
                "date": e.date or "Date not recorded",
                "standard": s.number if s else e.standard_id,
                "standardId": e.standard_id,
                "change": CHANGE_LABEL.get(e.kind, e.kind),
                "summary": e.summary,
                "severity": e.severity,
                "affected": _affected(documents, e.standard_id, dag, corpus),
            }
        )
    rank = {"high": 0, "medium": 1, "low": 2}
    events.sort(key=lambda ev: (-int(bool(ev["affected"])), rank[ev["severity"]]))
    return events


@router.get("/corpus/status")
def corpus_status():
    loaded = get_corpus()
    corpus = loaded.corpus
    return {
        "version": corpus.version,
        "source": loaded.source,
        "clauses": sum(len(s.clauses) for s in corpus.standards),
        "relationships": len(corpus.relationships),
        "events": len(corpus.events),
        "standards": [
            {
                "id": s.id,
                "number": s.number,
                "title": s.title,
                "status": STATUS_LABEL.get(s.status, s.status),
                "category": s.category,
                "clauses": len(s.clauses),
                "verified": s.source.verified,
            }
            for s in corpus.standards
        ],
    }
