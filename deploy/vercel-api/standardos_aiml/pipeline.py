"""End-to-end analysis pipeline: parse → extract → map → reason → repair."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional, Union

from .config import PipelineConfig, current, current as active_config, use_config
from .ingest.parse import page_locator, parse_document
from .ingest.sections import detect_sections
from .nlp.requirements import extract_requirements
from .provenance import js_round
from .reasoning.certification import certification_findings
from .reasoning.conflicts import (
    check_constraints,
    constraint_conflict_findings,
    intra_document_conflicts,
    reference_edition_conflicts,
)
from .reasoning.context import Applicability, ReasoningContext
from .reasoning.dependencies import dependency_gaps
from .reasoning.gaps import checklist_gaps, vague_requirement_findings
from .reasoning.repair import generate_repairs
from .reasoning.verification import verification_findings
from .reasoning.versions import version_findings
from .standards.dag import DependencyDAG
from .standards.graph import StandardsGraph, build_analysis_graph
from .standards.resolve import ResolvedReference
from .standards.retrieval import DEFAULT_RETRIEVAL, RetrievalOptions, StandardsIndex, document_context_terms
from .types import (
    STAGES,
    AnalysisResult,
    Corpus,
    ParsedDocument,
    Readiness,
    ReasoningFinding,
    RequirementMapping,
)
from .version import PIPELINE_VERSION

# Pasted text (str), an upload ((bytes, filename)) or an already parsed document.
PipelineInput = Union[str, tuple[bytes, str], ParsedDocument]
StageCallback = Callable[[str, int], None]


@dataclass
class Engine:
    index: StandardsIndex
    graph: StandardsGraph
    dag: DependencyDAG


_engine_cache: dict[str, Engine] = {}


def get_engine(corpus: Corpus) -> Engine:
    """One index per corpus version; building it is the only non-trivial setup cost."""
    engine = _engine_cache.get(corpus.version)
    if engine is None:
        graph = StandardsGraph(corpus)
        engine = Engine(StandardsIndex(corpus), graph, DependencyDAG(corpus, graph))
        _engine_cache.clear()
        _engine_cache[corpus.version] = engine
    return engine


SEVERITY_PENALTY = {"high": 8, "medium": 3, "low": 1}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
KIND_ORDER = {"conflicting": 0, "outdated": 1, "missing": 2, "certification": 3, "verified": 4}


def run_pipeline(
    source: PipelineInput,
    corpus: Corpus,
    retrieval: Optional[RetrievalOptions] = None,
    on_stage: Optional[StageCallback] = None,
    config: Optional[PipelineConfig] = None,
) -> AnalysisResult:
    """Analyse one document. ``config`` defaults to the context's configuration (see config.py)."""
    cfg = config or current()
    with use_config(cfg):
        return _run(source, corpus, retrieval or cfg.retrieval, on_stage, cfg)


def _run(
    source: PipelineInput,
    corpus: Corpus,
    options: RetrievalOptions,
    on_stage: Optional[StageCallback],
    cfg: PipelineConfig,
) -> AnalysisResult:
    timings: dict[str, float] = {}
    tracker: dict[str, object] = {"current": None, "start": time.perf_counter()}

    def stage(name: str) -> None:
        current = tracker["current"]
        if current:
            timings[str(current)] = js_round((time.perf_counter() - float(tracker["start"])) * 1000, 1)
        tracker["current"] = name
        tracker["start"] = time.perf_counter()
        if on_stage:
            on_stage(name, STAGES.index(name) + 1)

    # 1. Read
    stage("reading")
    document = source if isinstance(source, ParsedDocument) else parse_document(source)
    page_at = page_locator(document)

    # 2. Extract requirements
    stage("extracting")
    sections = detect_sections(document.text, page_at)
    requirements = extract_requirements(document.text, sections, page_at)
    if active_config().classifier != "lexicon":
        from .ml.classifier import reclassify

        reclassify(requirements, active_config().classifier)

    # 3. Categorise: document-level product context and qualifiers
    stage("categorising")
    context_terms = document_context_terms(requirements)
    qualifiers: dict[str, list[str]] = {}
    for req in requirements:
        for a in req.attributes:
            if a.parameter in ("exposure_condition", "steel_grade") and a.text:
                values = qualifiers.setdefault(a.parameter, [])
                if a.text not in values:
                    values.append(a.text)

    # 4. Map requirements to standards and clauses
    stage("mapping")
    engine = get_engine(corpus)
    index, graph = engine.index, engine.graph
    resolved: dict[str, list[ResolvedReference]] = {
        req.id: [index.resolver.resolve(r) for r in req.references] for req in requirements
    }
    document_cited = {r.standard_id for refs in resolved.values() for r in refs if r.standard_id}
    mappings: list[RequirementMapping] = []
    for req in requirements:
        refs = resolved.get(req.id, [])
        hits = index.retrieve(req, [r for r in refs if r.standard_id], context_terms, options, document_cited)
        cited = {r.standard_id for r in refs}
        basis = ("explicit_reference" if hits[0].standard_id in cited else "retrieval") if hits else "none"
        mappings.append(RequirementMapping(req.id, hits, basis))

    # 5. Resolve applicability, dependencies and the evidence graph
    stage("resolving")
    applicability: dict[str, Applicability] = {}

    def note(standard_id: str, confidence: float, explicit: bool, requirement_id: str) -> None:
        prev = applicability.get(standard_id) or Applicability(standard_id, 0.0, False, [])
        prev.confidence = max(prev.confidence, confidence)
        prev.explicit = prev.explicit or explicit
        if requirement_id not in prev.requirement_ids:
            prev.requirement_ids.append(requirement_id)
        applicability[standard_id] = prev

    for m in mappings:
        top = m.hits[0] if m.hits else None
        if top and top.confidence >= options.min_confidence:
            note(top.standard_id, top.confidence, False, m.requirement_id)
    for req_id, refs in resolved.items():
        for r in refs:
            if r.standard_id:
                note(r.standard_id, r.provenance.confidence, True, req_id)
    applicable_ids = [
        a.standard_id for a in sorted(applicability.values(), key=lambda a: (-int(a.explicit), -a.confidence))
    ]
    ctx = ReasoningContext(
        corpus=corpus,
        graph=graph,
        resolver=index.resolver,
        requirements=requirements,
        mappings=mappings,
        resolved=resolved,
        applicability=applicability,
        qualifiers=qualifiers,
        threshold=options.min_confidence,
        index=index,
        dag=engine.dag,
        context_terms=context_terms,
    )

    # 6. Certifications
    stage("certifications")
    certification = certification_findings(ctx)

    # 7. Conflicts, gaps, dependencies, versions
    stage("conflicts")
    checks = check_constraints(ctx)
    conflicts = [
        *constraint_conflict_findings(checks),
        *intra_document_conflicts(ctx),
        *reference_edition_conflicts(ctx),
    ]
    versions = version_findings(ctx)
    gaps = checklist_gaps(ctx)
    consumed = {g.requirement_id for g in gaps if g.requirement_id}
    dependencies = dependency_gaps(ctx, consumed)
    vague = vague_requirement_findings(ctx, consumed)
    problems = [*conflicts, *versions, *gaps, *dependencies, *certification, *vague]
    flagged = {f.requirement_id for f in problems if f.kind in ("conflicting", "outdated") and f.requirement_id}
    verified = verification_findings(ctx, checks, flagged)

    # 8. Report: order, number, repair, score
    stage("reporting")
    findings: list[ReasoningFinding] = sorted(
        [*problems, *verified], key=lambda f: (KIND_ORDER[f.kind], SEVERITY_ORDER[f.severity])
    )
    for i, f in enumerate(findings):
        f.id = f"f-{i + 1}"
    repairs = generate_repairs(ctx, findings, checks)
    for i, r in enumerate(repairs):
        r.id = f"rp-{i + 1}"
    graph_out = build_analysis_graph(corpus, graph, requirements, mappings, applicable_ids)
    readiness = compute_readiness(len(requirements), mappings, findings, options.min_confidence)
    current = tracker["current"]
    if current:
        timings[str(current)] = js_round((time.perf_counter() - float(tracker["start"])) * 1000, 1)

    return AnalysisResult(
        pipeline_version=PIPELINE_VERSION,
        config_name=cfg.name,
        corpus_version=corpus.version,
        document=document,
        sections=sections,
        requirements=requirements,
        mappings=mappings,
        applicable_standard_ids=applicable_ids,
        graph=graph_out,
        findings=findings,
        repairs=repairs,
        readiness=readiness,
        timings_ms=timings,
    )


def compute_readiness(
    total: int, mappings: list[RequirementMapping], findings: list[ReasoningFinding], threshold: float
) -> Readiness:
    """Mapping coverage minus a severity-weighted penalty for open issues.

    A triage heuristic, not a compliance probability.
    """
    mapped = sum(
        1
        for m in mappings
        if (m.hits[0].confidence if m.hits else 0) >= threshold or m.basis == "explicit_reference"
    )
    coverage = mapped / total if total else 0
    counts = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        if f.kind != "verified":
            counts[f.severity] += 1
    penalty = sum(counts[s] * SEVERITY_PENALTY[s] for s in counts)
    score = int(js_round(max(0.0, min(100.0, coverage * 100 - penalty)), 0))
    return Readiness(
        score=score,
        formula=(
            f"round(clamp(100 × mapped/total − ({SEVERITY_PENALTY['high']} × high + {SEVERITY_PENALTY['medium']} × medium"
            f" + {SEVERITY_PENALTY['low']} × low open findings), 0, 100))"
        ),
        inputs={
            "total": total,
            "mapped": mapped,
            "coverage": js_round(coverage),
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"],
            "penalty": penalty,
        },
    )
