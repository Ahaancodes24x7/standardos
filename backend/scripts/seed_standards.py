"""Load a standards corpus into Postgres and mark it active.

    uv run python -m scripts.seed_standards              # bundled seed corpus
    uv run python -m scripts.seed_standards corpus.json  # a camelCase corpus export (same shape as the seed)

Run from ``backend/`` after ``alembic upgrade head``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from standardos_aiml.standards.seed import corpus_from_payload, seed_corpus

from app.corpus import import_corpus
from app.db import session_scope


def main(argv: list[str]) -> None:
    if argv:
        path = Path(argv[0])
        corpus = corpus_from_payload(json.loads(path.read_text(encoding="utf-8")))
        source = f"import:{path.name}"
    else:
        corpus = seed_corpus()
        source = "curated-seed"
    with session_scope() as db:
        import_corpus(db, corpus, source)
    print(
        f"Loaded corpus {corpus.version}: {len(corpus.standards)} standards, "
        f"{sum(len(s.clauses) for s in corpus.standards)} clauses, {len(corpus.relationships)} relationships, "
        f"{len(corpus.events)} version events."
    )


if __name__ == "__main__":
    main(sys.argv[1:])
