"""The account-less demo workspace: the real pipeline over bundled sample specifications.

Nothing is persisted; results are cached per corpus version.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from standardos_aiml.pipeline import run_pipeline
from standardos_aiml.samples import SAMPLE_DOCUMENTS

from .corpus import get_corpus
from .view import build_document_analysis, snapshot_from_result
from .engine import pipeline_config

_cache: dict[str, Any] = {}
_lock = threading.Lock()


def sample_workspace() -> list[dict[str, Any]]:
    loaded = get_corpus()
    with _lock:
        if _cache.get("version") == loaded.corpus.version:
            return _cache["documents"]
        analyzed_at = datetime.now(timezone.utc).isoformat()
        documents = [
            build_document_analysis(
                snapshot_from_result(
                    run_pipeline(sample.text, loaded.corpus, config=pipeline_config()),
                    documentId=sample.id,
                    name=sample.name,
                    organization=sample.organization,
                    type=sample.type,
                    analyzedAt=analyzed_at,
                    isSample=True,
                    corpusSource=loaded.source,
                ),
                loaded.corpus,
            )
            for sample in SAMPLE_DOCUMENTS
        ]
        _cache.update(version=loaded.corpus.version, documents=documents)
        return documents
