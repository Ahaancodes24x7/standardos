"""Positive evidence.

"Verified" findings record a requirement value that was checked against a
clause limit and found inside it, or a citation of the current edition of a
standard. A requirement that also has a problem finding is never marked
verified.
"""

from __future__ import annotations

from ..nlp.units import format_canonical
from ..provenance import provenance
from ..types import Evidence, ReasoningFinding
from .conflicts import ConstraintCheck, describe_quantity
from .context import ReasoningContext, clause_evidence, clause_label, label, requirement_evidence, standard_by_id


def verification_findings(
    ctx: ReasoningContext, checks: list[ConstraintCheck], flagged: set[str]
) -> list[ReasoningFinding]:
    out: list[ReasoningFinding] = []
    done: set[str] = set()
    violated = {c.requirement.id for c in checks if c.violation != "none"}

    for check in checks:
        req = check.requirement
        if check.violation != "none" or req.id in flagged or req.id in done or req.id in violated:
            continue
        done.add(req.id)
        std, clause, constraint = check.standard, check.clause, check.constraint
        bound = " and ".join(
            part
            for part in (
                f"≥ {format_canonical(constraint.min, constraint.unit)}" if constraint.min is not None else "",
                f"≤ {format_canonical(constraint.max, constraint.unit)}" if constraint.max is not None else "",
            )
            if part
        )
        stated = describe_quantity(check.quantity)
        out.append(
            ReasoningFinding(
                id="",
                kind="verified",
                rule="constraint_satisfied",
                title=f"{label(check.parameter)} is within {std.designation} limits",
                severity="low",
                requirement_id=req.id,
                requirement_text=req.text,
                standard_id=std.id,
                clause_id=clause.id,
                standard_label=clause_label(std, clause),
                reason=f"The stated {label(check.parameter).lower()} ({stated}) satisfies {bound} for {constraint.condition}.",
                action="Retain the requirement; keep the verification record with the technical evaluation.",
                evidence=[
                    requirement_evidence(req),
                    clause_evidence(std, clause),
                    Evidence(
                        kind="constraint_check",
                        label="Interval check",
                        excerpt=f"{stated} lies within {bound}.",
                        requirement_id=req.id,
                        span=check.quantity.span,
                        standard_id=std.id,
                        clause_id=clause.id,
                    ),
                ],
                provenance=provenance(
                    "reasoning.verification", "constraint", 0.85, [f"{check.parameter} checked against {clause.id}"]
                ),
            )
        )

    for req in ctx.requirements:
        if req.id in flagged or req.id in done:
            continue
        current = None
        for r in ctx.resolved.get(req.id, []):
            std = standard_by_id(ctx, r.standard_id)
            if (
                std
                and std.status not in ("superseded", "withdrawn")
                and r.edition in ("current", "unspecified")
                and r.provenance.confidence >= 0.9
            ):
                current = r
                break
        std = standard_by_id(ctx, current.standard_id) if current else None
        if not current or not std:
            continue
        done.add(req.id)
        unspecified = current.edition == "unspecified"
        out.append(
            ReasoningFinding(
                id="",
                kind="verified",
                rule="current_reference",
                title=f"Reference to {std.number} is current",
                severity="low",
                requirement_id=req.id,
                requirement_text=req.text,
                standard_id=std.id,
                clause_id=None,
                standard_label=std.number,
                reason=(
                    f"{current.reference.raw} resolves to {std.number}, which the corpus records as {std.status}."
                    + (" No edition year is cited, so the latest edition applies by default." if unspecified else "")
                ),
                action=f"Consider citing the edition explicitly ({std.number})." if unspecified else "Retain the reference.",
                evidence=[requirement_evidence(req), clause_evidence(std, std.clauses[0] if std.clauses else None)],
                provenance=provenance(
                    "reasoning.verification",
                    "rule",
                    current.provenance.confidence * 0.9,
                    current.provenance.signals,
                ),
            )
        )
    return out
