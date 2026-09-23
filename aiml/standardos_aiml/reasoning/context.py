"""Shared state and helpers for the reasoning detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

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

    def mapping_for(self, requirement_id: str) -> Optional[RequirementMapping]:
        return next((m for m in self.mappings if m.requirement_id == requirement_id), None)

    def requirement(self, requirement_id: Optional[str]) -> Optional[StructuredRequirement]:
        if not requirement_id:
            return None
        return next((r for r in self.requirements if r.id == requirement_id), None)


def strong_applicable(ctx: ReasoningContext) -> list[Applicability]:
    """Standards that clearly apply: cited, or the top match of a requirement at ≥ 0.5 confidence."""
    return [a for a in ctx.applicability.values() if a.explicit or a.confidence >= 0.5]


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
