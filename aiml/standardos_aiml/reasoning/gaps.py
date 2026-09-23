"""Requirement-gap detection.

Each standard in the corpus carries a checklist of the information a
purchaser must state when invoking it (e.g. the duty point for a pump, the
exposure condition for concrete). Limits the standard fixes itself (pH range,
cable voltage grade) are NOT checklist items — citing the standard already
imports them.

A checklist item is:

* satisfied    — some requirement states a value for the parameter
* insufficient — the parameter is mentioned but never given a measurable value
* missing      — the parameter is not mentioned at all
"""

from __future__ import annotations

from ..provenance import provenance
from ..types import ReasoningFinding
from .context import (
    ReasoningContext,
    clause_by_id,
    clause_evidence,
    clause_label,
    document_attributes,
    has_value,
    requirement_evidence,
    standard_by_id,
    strong_applicable,
)


def checklist_gaps(ctx: ReasoningContext) -> list[ReasoningFinding]:
    out: list[ReasoningFinding] = []
    reported: set[str] = set()
    for app in strong_applicable(ctx):
        std = standard_by_id(ctx, app.standard_id)
        if not std:
            continue
        # A single passing reference to a code of practice (e.g. "earthing to
        # IS 3043") does not make the specification responsible for everything
        # the code leaves to the designer; require it to govern ≥ 2 requirements.
        if std.kind == "code_of_practice" and len(app.requirement_ids) < 2:
            continue
        has_test_dependency = len(ctx.graph.outgoing(std.id, ["TESTED_BY"])) > 0
        anchor = next((r for r in ctx.requirements if r.id in app.requirement_ids), None)
        for item in std.checklist:
            # Test-method gaps for standards with a TESTED_BY edge are reported by
            # dependency reasoning, which can name the test standard.
            if item.parameter == "test_method" and has_test_dependency:
                continue
            if item.parameter in reported:
                continue
            attrs = document_attributes(ctx, item.parameter)
            if any(has_value(attr) for _, attr in attrs):
                continue
            mentioned = attrs[0][0] if attrs else None
            if not mentioned and item.severity == "low":
                continue
            reported.add(item.parameter)
            clause = clause_by_id(ctx, item.clause_id)
            evidence = [clause_evidence(std, clause)]
            if mentioned:
                evidence.insert(0, requirement_evidence(mentioned, "Requirement mentioning it without a value"))
            if anchor and anchor is not mentioned:
                evidence.append(requirement_evidence(anchor, f"Why {std.number} applies"))
            basis = "cited" if app.explicit else f"retrieval confidence {app.confidence:.2f}"
            state = "mentioned without value" if mentioned else "absent"
            out.append(
                ReasoningFinding(
                    id="",
                    kind="missing",
                    rule="insufficient_specification" if mentioned else "checklist_gap",
                    parameter=item.parameter,
                    title=f"{item.label} is not measurable" if mentioned else f"{item.label} is unspecified",
                    severity=item.severity,
                    requirement_id=(mentioned.id if mentioned else (anchor.id if anchor else None)),
                    requirement_text=(
                        mentioned.text if mentioned else (anchor.text if anchor else f"Specification invokes {std.number}")
                    ),
                    standard_id=std.id,
                    clause_id=item.clause_id,
                    standard_label=clause_label(std, clause),
                    reason=(
                        f"{item.rationale} "
                        + (
                            "The specification refers to it but gives no measurable value."
                            if mentioned
                            else "No requirement in the specification states it."
                        )
                    ),
                    action=f"Add a measurable requirement for {item.label.lower()} referencing {std.number}.",
                    evidence=evidence,
                    provenance=provenance(
                        "reasoning.gaps",
                        "rule",
                        0.75 if mentioned else 0.7,
                        [
                            f"{std.number} applies ({basis})",
                            f"checklist item {item.parameter} {state} across {len(ctx.requirements)} requirements",
                        ],
                    ),
                )
            )
    return out


def vague_requirement_findings(ctx: ReasoningContext, covered: set[str]) -> list[ReasoningFinding]:
    """Requirements worded vaguely ("suitable", "energy efficient") that no checklist gap already covers."""
    out: list[ReasoningFinding] = []
    for req in ctx.requirements:
        if not req.vague or req.id in covered:
            continue
        mapping = ctx.mapping_for(req.id)
        top = mapping.hits[0] if mapping and mapping.hits else None
        std = standard_by_id(ctx, top.standard_id) if top and top.confidence >= ctx.threshold else None
        clause = clause_by_id(ctx, top.clause_id if top else None) if std else None
        closest = f" The closest governing standard is {std.number}." if std else ""
        out.append(
            ReasoningFinding(
                id="",
                kind="missing",
                rule="vague_requirement",
                title="Requirement is not measurable",
                severity="low",
                requirement_id=req.id,
                requirement_text=req.text,
                standard_id=std.id if std else None,
                clause_id=clause.id if clause else None,
                standard_label=clause_label(std, clause) if std else "Specification quality check",
                reason=(
                    "The requirement uses qualitative wording without a value, reference or acceptance criterion, "
                    f"so compliance cannot be verified.{closest}"
                ),
                action=(
                    "Replace the qualitative wording with a measurable value, a referenced standard clause, "
                    "or an acceptance test."
                ),
                evidence=[requirement_evidence(req), clause_evidence(std, clause)] if std else [requirement_evidence(req)],
                provenance=provenance(
                    "reasoning.gaps", "rule", 0.65, [s for s in req.provenance.signals if s.startswith("vague")]
                ),
            )
        )
    return out
