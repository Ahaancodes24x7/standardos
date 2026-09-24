"""Apply a trained requirement classifier inside the pipeline.

Selected with ``PipelineConfig.classifier``; ``lexicon`` (the default) never
touches this module. Models are trained by ``python -m evaluation.classifiers``
and read from ``aiml/models/requirement-classifier``. When the ``ml`` extra is
not installed, or the models have not been trained, the lexicon category is
kept and the provenance says so.
"""

from __future__ import annotations

import functools
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from ..types import StructuredRequirement
from .features import CATEGORIES

log = logging.getLogger(__name__)

MODEL_DIR = Path(os.environ.get("STANDARDOS_MODEL_DIR", Path(__file__).resolve().parents[2] / "models" / "requirement-classifier"))


@functools.lru_cache(maxsize=1)
def _load() -> Optional[dict[str, Any]]:
    try:
        import joblib
        import torch

        from .models import build_hybrid

        meta = json.loads((MODEL_DIR / "meta.json").read_text(encoding="utf-8"))
        hybrid = build_hybrid()
        hybrid.load_state_dict(torch.load(MODEL_DIR / "hybrid-nn.pt", map_location="cpu"))
        hybrid.eval()
        return {
            "meta": meta,
            "tfidf-lr": joblib.load(MODEL_DIR / "tfidf-lr.joblib"),
            "embed-lr": joblib.load(MODEL_DIR / "embed-lr.joblib"),
            "hybrid-nn": hybrid,
        }
    except Exception as exc:  # missing extra or untrained models
        log.warning("requirement classifier unavailable (%s); keeping lexicon categories", exc)
        return None


def available() -> bool:
    return _load() is not None


def reclassify(requirements: list[StructuredRequirement], method: str) -> None:
    """Replace lexicon categories with ``method``'s predictions, in place."""
    if method == "lexicon" or not requirements:
        return
    models = _load()
    if models is None:
        for req in requirements:
            req.provenance.signals.append(f"classifier {method} unavailable — lexicon category kept")
        return

    from .features import lexicon_scores, struct_vector, structure
    from .models import ENCODER, embed, predict_hybrid

    import numpy as np

    texts = [r.text for r in requirements]
    if method == "tfidf-lr":
        probs = models["tfidf-lr"].predict_proba(texts)
    else:
        emb = embed(texts).astype(np.float32)
        if method == "embed-lr":
            probs = models["embed-lr"].predict_proba(emb)
        else:
            structured = [structure(t) for t in texts]
            probs = predict_hybrid(models["hybrid-nn"], emb, np.array([struct_vector(s) for s in structured], dtype=np.float32))
    tau = float(models["meta"]["gate_tau"])

    for req, p in zip(requirements, probs):
        best = int(p.argmax())
        category, source = CATEGORIES[best], method
        if method == "gated":
            _, lex_category, lex_conf = lexicon_scores(structure(req.text))
            if lex_conf >= tau:
                category, source = lex_category, f"gated→lexicon (confidence {lex_conf:.2f} ≥ τ {tau:.2f})"
            else:
                source = f"gated→hybrid-nn (lexicon confidence {lex_conf:.2f} < τ {tau:.2f})"
        if category != req.category:
            req.provenance.signals.append(f"lexicon said {req.category}")
        req.category = category
        req.category_scores = {c: round(float(v), 4) for c, v in zip(CATEGORIES, p)}
        req.provenance.signals.append(f"category {category} by {source} (p={float(p[best]):.2f})")
        req.provenance.model = ENCODER if method != "tfidf-lr" else "tfidf-lr"
