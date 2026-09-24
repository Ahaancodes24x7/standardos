"""Standards corpus: loaded from Postgres, falling back to the bundled seed.

The corpus lives in Postgres (standards, standard_clauses,
standard_relationships, standard_version_events, standard_prior_editions). It
is loaded into memory once per corpus version: at a few hundred clauses the
whole index is well under a megabyte and in-memory BM25 answers in about a
millisecond. With no active corpus (fresh install, before
``python -m scripts.seed_standards``), the bundled seed is used and every run
records corpus source "bundled-seed".
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from standardos_aiml.serialize import to_wire
from standardos_aiml.standards.seed import corpus_from_payload, seed_corpus
from standardos_aiml.types import Corpus

from . import models as m
from .db import database_configured, session_scope

log = logging.getLogger(__name__)

TTL_SECONDS = 300


@dataclass
class LoadedCorpus:
    corpus: Corpus
    source: str  # database | bundled-seed


_cache: dict[str, object] = {}
_lock = threading.Lock()


def get_corpus() -> LoadedCorpus:
    with _lock:
        cached = _cache.get("value")
        if cached and time.monotonic() - float(_cache["at"]) < TTL_SECONDS:  # type: ignore[arg-type]
            return cached  # type: ignore[return-value]
        value: LoadedCorpus
        try:
            loaded = _load_from_database() if database_configured() else None
            value = loaded or LoadedCorpus(seed_corpus(), "bundled-seed")
        except Exception:  # database unreachable: keep serving with the seed
            log.exception("[corpus] failed to load from database; using bundled seed")
            value = LoadedCorpus(seed_corpus(), "bundled-seed")
        _cache.update(value=value, at=time.monotonic())
        return value


def invalidate_corpus_cache() -> None:
    with _lock:
        _cache.clear()


def _load_from_database() -> LoadedCorpus | None:
    with session_scope() as db:
        active = db.scalar(select(m.CorpusVersion).where(m.CorpusVersion.is_active.is_(True)))
        if not active:
            return None
        standards = db.scalars(select(m.Standard)).all()
        clauses = db.scalars(select(m.StandardClause).order_by(m.StandardClause.standard_id, m.StandardClause.ordinal)).all()
        rels = db.scalars(select(m.StandardRelationship)).all()
        events = db.scalars(select(m.StandardVersionEvent)).all()
        priors = db.scalars(select(m.StandardPriorEdition)).all()
        by_std: dict[str, list[dict]] = {}
        for c in clauses:
            by_std.setdefault(c.standard_id, []).append(
                {"id": c.id, "standardId": c.standard_id, "ref": c.ref, "heading": c.heading, "text": c.text,
                 "constraints": c.constraints}
            )
        payload = {
            "standards": [
                {
                    "id": s.id, "designation": s.designation, "year": s.year, "number": s.number, "title": s.title,
                    "scope": s.scope, "category": s.category, "kind": s.kind, "status": s.status,
                    "aliases": s.aliases, "keywords": s.keywords, "certification": s.certification,
                    "checklist": s.checklist, "source": s.source, "clauses": by_std.get(s.id, []),
                }
                for s in standards
            ],
            "relationships": [
                {"id": r.id, "type": r.type, "fromId": r.from_standard_id, "toId": r.to_standard_id,
                 "clauseId": r.clause_id, "confidence": r.confidence, "method": r.method, "note": r.note}
                for r in rels
            ],
            "events": [
                {"id": e.id, "standardId": e.standard_id, "date": e.date, "kind": e.kind, "summary": e.summary,
                 "severity": e.severity, "replacedById": e.replaced_by_id}
                for e in events
            ],
            "priorEditions": [
                {"designation": p.designation, "year": p.year, "replacedById": p.replaced_by_id} for p in priors
            ],
        }
        return LoadedCorpus(corpus_from_payload(payload, version=active.version), "database")


def import_corpus(db: Session, corpus: Corpus, source: str) -> None:
    """Replace the stored corpus with ``corpus`` in one transaction and mark it active."""
    db.execute(delete(m.StandardPriorEdition))
    db.execute(delete(m.StandardVersionEvent))
    db.execute(delete(m.StandardRelationship))
    db.execute(delete(m.StandardClause))
    db.execute(delete(m.Standard))
    db.flush()
    for s in corpus.standards:
        w = to_wire(s)
        db.add(
            m.Standard(
                id=s.id, designation=s.designation, year=s.year, number=s.number, title=s.title, scope=s.scope,
                category=s.category, kind=s.kind, status=s.status, aliases=s.aliases, keywords=s.keywords,
                certification=w["certification"], checklist=w["checklist"], source=w["source"],
                corpus_version=corpus.version,
            )
        )
    db.flush()
    for s in corpus.standards:
        for i, c in enumerate(s.clauses):
            db.add(
                m.StandardClause(
                    id=c.id, standard_id=s.id, ordinal=i, ref=c.ref, heading=c.heading, text=c.text,
                    constraints=to_wire(c.constraints),
                )
            )
    for r in corpus.relationships:
        db.add(
            m.StandardRelationship(
                id=r.id, type=r.type, from_standard_id=r.from_id, to_standard_id=r.to_id, clause_id=r.clause_id,
                confidence=r.confidence, method=r.method, note=r.note,
            )
        )
    for e in corpus.events:
        db.add(
            m.StandardVersionEvent(
                id=e.id, standard_id=e.standard_id, date=e.date, kind=e.kind, summary=e.summary,
                severity=e.severity, replaced_by_id=e.replaced_by_id,
            )
        )
    for p in corpus.prior_editions:
        db.add(m.StandardPriorEdition(designation=p.designation, year=p.year, replaced_by_id=p.replaced_by_id))
    db.execute(update(m.CorpusVersion).values(is_active=False))
    stmt = pg_insert(m.CorpusVersion).values(
        version=corpus.version, source=source, standard_count=len(corpus.standards),
        relationship_count=len(corpus.relationships), is_active=True,
    )
    db.execute(
        stmt.on_conflict_do_update(
            index_elements=[m.CorpusVersion.version],
            set_={"is_active": True, "source": source, "loaded_at": stmt.excluded.loaded_at},
        )
    )
    db.commit()
    invalidate_corpus_cache()
