"""Engine configuration and named presets.

Every behavioural change made after the 2.1.0 audit sits behind a flag here, so
the evaluation framework can score the old and new behaviour on the same data
in the same codebase:

* ``legacy-2.1`` reproduces standardos-pipeline/2.1.0-py exactly;
* ``v3`` is the current default (all audit fixes on, lexicon classifier);
* further presets are experiments (DAG dependency reasoning, neural classifier).

``PipelineConfig.name`` is recorded in every analysis result and evaluation run.
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Iterator


@dataclass(frozen=True)
class RetrievalOptions:
    expansion: bool = False  # use the domain thesaurus for query expansion
    document_context: bool = True  # add the document's dominant product terms to every query
    rerank: bool = True  # apply the feature re-ranker; when False, rank by BM25 only
    min_confidence: float = 0.35  # hits below this confidence are not returned as mappings
    top_k: int = 5


@dataclass(frozen=True)
class PipelineConfig:
    name: str = "v3"
    retrieval: RetrievalOptions = field(default_factory=RetrievalOptions)

    # Phase 1 — extraction and classification
    zoning: bool = True  # exclude NIT/ITB/commercial/BOQ zones from requirement identification
    heading_v2: bool = True  # "SECTION IV – 11 kV POWER CABLES" is a heading, not a requirement
    segmentation_v2: bool = True  # split after unit abbreviations ("90 deg C. Next"); "1600 A" at line end is not the article "a"
    attributes_v2: bool = True  # a test/verification clause citing a standard states its test method
    lexicon_version: int = 2  # classification cue lexicon (1 = 2.1.0)
    units_v2: bool = True  # MLD/KLD, lm/W, Deg.C, Volts … surface forms
    classifier: str = "lexicon"  # lexicon | tfidf-lr | embed-lr | hybrid-nn | gated

    # Phase 2 — retrieval
    rerank_version: int = 2  # parameter features only break BM25 near-ties; role-based test credit
    product_terms_v2: bool = True  # extra product surface forms; requirements inherit their section heading's products
    scope_guard: bool = True  # prefer a standard the document cites for the same product

    # Phase 3 — reasoning
    dependency_mode: str = "citation"  # legacy | citation | dag
    detector_gate: bool = True  # retrieval-only mappings need ≥ 0.5 and product scope to raise findings
    scoped_checklists: bool = True  # checklist items are checked against the standard's own requirements
    vague_version: int = 2
    amendment_dedupe: bool = True  # one amendment reminder per standard per document
    certification_scope: bool = True  # conformity evidence must cover each product standard, not just exist somewhere

    # Relation extraction (evaluation / curation only; not on the runtime path)
    relations_version: int = 2

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def with_(self, **changes: Any) -> "PipelineConfig":
        return replace(self, **changes)


LEGACY_2_1 = PipelineConfig(
    name="legacy-2.1",
    zoning=False,
    heading_v2=False,
    segmentation_v2=False,
    attributes_v2=False,
    lexicon_version=1,
    units_v2=False,
    classifier="lexicon",
    rerank_version=1,
    product_terms_v2=False,
    scope_guard=False,
    dependency_mode="legacy",
    detector_gate=False,
    scoped_checklists=False,
    vague_version=1,
    amendment_dedupe=False,
    certification_scope=False,
    relations_version=1,
)

V3 = PipelineConfig(name="v3")

PRESETS: dict[str, PipelineConfig] = {
    "legacy-2.1": LEGACY_2_1,
    "v3": V3,
    # Dependency-reasoning experiments
    "v3-dep-legacy": V3.with_(name="v3-dep-legacy", dependency_mode="legacy"),
    "v3-dag": V3.with_(name="v3-dag", dependency_mode="dag"),
    # Classifier experiments (require the `ml` extra and a trained model)
    "v3-hybrid": V3.with_(name="v3-hybrid", classifier="hybrid-nn"),
    "v3-gated": V3.with_(name="v3-gated", classifier="gated"),
    "v3-tfidf": V3.with_(name="v3-tfidf", classifier="tfidf-lr"),
    # Single-fix ablations on top of legacy, to attribute gains
    "legacy+extraction": LEGACY_2_1.with_(name="legacy+extraction", zoning=True, heading_v2=True, segmentation_v2=True, attributes_v2=True),
    "legacy+lexicon2": LEGACY_2_1.with_(name="legacy+lexicon2", lexicon_version=2, units_v2=True),
    "legacy+rerank2": LEGACY_2_1.with_(name="legacy+rerank2", rerank_version=2, product_terms_v2=True),
    "legacy+gating": LEGACY_2_1.with_(
        name="legacy+gating", detector_gate=True, scope_guard=True, scoped_checklists=True, certification_scope=True
    ),
    "legacy+dep-citation": LEGACY_2_1.with_(name="legacy+dep-citation", dependency_mode="citation"),
}

DEFAULT = V3


def preset(name: str) -> PipelineConfig:
    try:
        return PRESETS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown pipeline preset {name!r}; choose from {', '.join(PRESETS)}") from exc


_current: contextvars.ContextVar[PipelineConfig] = contextvars.ContextVar("standardos_config", default=DEFAULT)


def current() -> PipelineConfig:
    """The configuration of the analysis running in this context (DEFAULT outside one)."""
    return _current.get()


@contextmanager
def use_config(config: PipelineConfig) -> Iterator[PipelineConfig]:
    token = _current.set(config)
    try:
        yield config
    finally:
        _current.reset(token)
