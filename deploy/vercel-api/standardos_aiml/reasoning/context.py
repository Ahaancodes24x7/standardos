"""Shared state and helpers for the reasoning detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..config import current

from ..nlp.parameters import parameter_label
from ..standards.graph import StandardsGraph
from ..standards.resolve import ResolvedReference, StandardResolver
from ..types import (
    Attribute,
    Corpus,
    CorpusClause,
    CorpusStandard,
    Evidence,
    RequirementMapping,
    StructuredRequirement,
)

label = parameter_label


@dataclass
class Applicability:
    standard_id: str
    confidence: float
    explicit: bool
    requirement_ids: list[str] = field(default_factory=list)  # requirements whose top hit is this standard, or that cite it


@dataclass
class ReasoningContext:
    """Everything the detectors need, computed once per analysis."""

    corpus: Corpus
    graph: StandardsGraph
    resolver: StandardResolver
    requirements: list[StructuredRequirement]
    mappings: list[RequirementMapping]
    resolved: dict[str, list[ResolvedReference]]
    applicability: dict[str, Applicability]  # per standard: why it applies to this document
    qualifiers: dict[str, list[str]]  # document-level qualifier values, e.g. exposure_condition → ["moderate"]
    threshold: float  # mapping confidence at or above which a requirement is considered mapped
    index: Any = None  # StandardsIndex (product-scope checks)
    dag: Any = None  # DependencyDAG
    context_terms: list[str] = field(default_factory=list)

    def mapping_for(self, requirement_id: str) -> Optional[RequirementMapping]:
        return next((m for m in self.mappings if m.requirement_id == requirement_id), None)

    def requirement(self, requirement_id: Optional[str]) -> Optional[StructuredRequirement]:
        if not requirement_id:
            return None
        return next((r for r in self.requirements if r.id == requirement_id), None)


GATE_CONFIDENCE = 0.5


def in_scope(ctx: ReasoningContext, req: Optional[StructuredRequirement], standard_id: str) -> bool:
    """Does the requirement (or, failing that, the document) name a product the standard covers?"""
    std = ctx.corpus.standard(standard_id)
    if std is None or ctx.index is None:
        return True
    terms = (req.terms if req else []) or ctx.context_terms
    if not terms:
        return True  # nothing to disagree with
    return any(ctx.index.matches_product(std, t) for t in terms)


def strong_applicable(ctx: ReasoningContext) -> list[Applicability]:
    """Standards that clearly apply: cited, or the top match of a requirement at ≥ 0.5 confidence.

    With the v3 detector gate, a retrieval-only standard must also be in product
    scope for at least one of the requirements that map to it.
    """
    out = []
    gate = current().detector_gate
    cited = cited_ids(ctx) if gate else set()
    for a in ctx.applicability.values():
        if a.explicit:
            out.append(a)
            continue
        if a.confidence < GATE_CONFIDENCE:
            continue
        if gate:
            std = ctx.corpus.standard(a.standard_id)
            # A code of practice binds only when the purchaser invokes it; a retrieval
            # match ("this clause is about earthing") is not an invocation.
            if std is not None and std.kind == "code_of_practice":
                continue
            reqs = [ctx.requirement(r) for r in a.requirement_ids]
            if not any(in_scope(ctx, r, a.standard_id) for r in reqs):
                continue
            # A competitor of a cited standard (IS 694 when the tender cites IS 7098 for its cables)
            # does not impose its own checklist or dependencies.
            if std is not None and ctx.index is not None and cited:
                terms = [t for r in reqs if r for t in r.terms] or ctx.context_terms
                # The standard it replaces (IS 8623 → IS/IEC 61439-1) is family, not a competitor.
                if ctx.index._cited_competitor(std, terms, cited - standard_family(ctx, a.standard_id)):
                    continue
        out.append(a)
    return out


def standard_family(ctx: ReasoningContext, standard_id: str) -> set[str]:
    """The standard plus what is read together with it: supersession relatives, its normative
    closure in the dependency DAG, and standards it directly references or relates to."""
    family = {standard_id}
    latest = ctx.graph.latest_replacement(standard_id)
    if latest:
        family.add(latest.id)
    for rel in ctx.graph.incoming(standard_id, ["SUPERSEDES"]) + ctx.graph.outgoing(standard_id, ["SUPERSEDES"]):
        family |= {rel.from_id, rel.to_id}
    for rel in ctx.graph.outgoing(standard_id, ["REFERENCES", "RELATED_TO"]) + ctx.graph.incoming(standard_id, ["RELATED_TO"]):
        family |= {rel.from_id, rel.to_id}
    if ctx.dag is not None:
        family |= set(ctx.dag.closure(standard_id))
        canon = ctx.dag.canon(standard_id)
        family |= {k for k, v in ctx.dag.canonical.items() if v == canon}
    return family


def cited_ids(ctx: ReasoningContext) -> set[str]:
    return {r.standard_id for refs in ctx.resolved.values() for r in refs if r.standard_id}


def requirements_for(ctx: ReasoningContext, standard_id: str) -> list[StructuredRequirement]:
    """Requirements that cite the standard or whose top mapping is it."""
    out = []
    for req in ctx.requirements:
        cites = any(r.standard_id == standard_id for r in ctx.resolved.get(req.id, []))
        m = ctx.mapping_for(req.id)
        top = m.hits[0] if m and m.hits else None
        if cites or (top and top.standard_id == standard_id and top.confidence >= ctx.threshold):
            out.append(req)
    return out


# Parameters that describe the whole supply/site rather than one item.
DOCUMENT_LEVEL = {
    "rated_voltage", "frequency", "ambient_temperature", "altitude", "relative_humidity", "exposure_condition", "earthing_system",
}


def standard_by_id(ctx: ReasoningContext, standard_id: Optional[str]) -> Optional[CorpusStandard]:
    return ctx.corpus.standard(standard_id)


def clause_by_id(ctx: ReasoningContext, clause_id: Optional[str]) -> Optional[CorpusClause]:
    if not clause_id:
        return None
    std = standard_by_id(ctx, clause_id.split("#")[0])
    return next((c for c in std.clauses if c.id == clause_id), None) if std else None


def clause_label(std: CorpusStandard, clause: Optional[CorpusClause]) -> str:
    if not clause:
        return std.number
    ref = f"Cl. {clause.ref} — " if clause.ref else ""
    return f"{std.number} · {ref}{clause.heading}"


def requirement_evidence(req: StructuredRequirement, title: str = "Source requirement") -> Evidence:
    section = f" ({req.section_label})" if req.section_label else ""
    page = f", p. {req.page}" if req.page else ""
    return Evidence(
        kind="requirement_text",
        label=f"{title}{section}{page}",
        excerpt=req.text,
        requirement_id=req.id,
        span=req.span,
    )


def clause_evidence(std: CorpusStandard, clause: Optional[CorpusClause]) -> Evidence:
    return Evidence(
        kind="standard_clause",
        label=clause_label(std, clause),
        excerpt=f"{clause.text} [paraphrased summary — consult the official text]" if clause else std.scope,
        standard_id=std.id,
        clause_id=clause.id if clause else None,
    )


def document_attributes(ctx: ReasoningContext, parameter: str) -> list[tuple[StructuredRequirement, Attribute]]:
    """Attributes across the whole document for a parameter."""
    return [(req, attr) for req in ctx.requirements for attr in req.attributes if attr.parameter == parameter]


def has_value(attr: Attribute) -> bool:
    return attr.quantity is not None or (attr.text is not None and attr.text != "")
