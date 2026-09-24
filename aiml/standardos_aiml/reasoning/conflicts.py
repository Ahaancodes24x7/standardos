"""Constraint reasoning with interval arithmetic.

Every requirement value and every clause limit is an interval in canonical
units; a conflict is a requirement interval that leaves the permitted
interval. Open ends of a requirement ("up to 50 °C") are treated as unstated,
not as ±∞, so a one-sided requirement is only checked on the side it states.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional

from ..nlp.units import format_canonical
from ..provenance import provenance
from ..types import (
    ClauseConstraint,
    CorpusClause,
    CorpusStandard,
    Evidence,
    Quantity,
    ReasoningFinding,
    StructuredRequirement,
)
from ..config import current
from .context import (
    GATE_CONFIDENCE,
    ReasoningContext,
    in_scope,
    clause_evidence,
    clause_label,
    document_attributes,
    label,
    requirement_evidence,
    standard_by_id,
)


@dataclass
class ConstraintCheck:
    requirement: StructuredRequirement
    quantity: Quantity
    parameter: str
    standard: CorpusStandard
    clause: CorpusClause
    constraint: ClauseConstraint
    violation: str  # none | partial | disjoint
    side: Optional[str]  # below | above | None


def fmt_bound(c: ClauseConstraint) -> str:
    if c.min is not None and c.max is not None:
        return f"{format_canonical(c.min, c.unit)} to {format_canonical(c.max, c.unit)}"
    if c.max is not None:
        return f"at most {format_canonical(c.max, c.unit)}"
    if c.min is not None:
        return f"at least {format_canonical(c.min, c.unit)}"
    return "unbounded"


def describe_quantity(q: Quantity) -> str:
    if q.comparator == "range" and q.min is not None and q.max is not None:
        return f"{format_canonical(q.min, q.unit)} to {format_canonical(q.max, q.unit)}"
    if q.comparator == "min" and q.min is not None:
        return f"at least {format_canonical(q.min, q.unit)}"
    if q.comparator == "max" and q.max is not None:
        return f"at most {format_canonical(q.max, q.unit)}"
    if q.comparator == "tolerance" and q.min is not None and q.max is not None and q.unit != "%":
        return f"{format_canonical(q.min, q.unit)} to {format_canonical(q.max, q.unit)}"
    value = q.value if q.value is not None else (q.min if q.min is not None else (q.max if q.max is not None else 0))
    return format_canonical(value, q.unit)


def compare(q: Quantity, c: ClauseConstraint) -> tuple[str, Optional[str]]:
    rmin, rmax = q.min, q.max
    below = (rmin is not None and c.min is not None and rmin < c.min) or (
        rmax is not None and c.min is not None and rmax < c.min and rmin is None
    )
    above = (rmax is not None and c.max is not None and rmax > c.max) or (
        rmin is not None and c.max is not None and rmin > c.max and rmax is None
    )
    if not below and not above:
        return "none", None
    entirely_outside = (rmax is not None and c.min is not None and rmax < c.min) or (
        rmin is not None and c.max is not None and rmin > c.max
    )
    return ("disjoint" if entirely_outside else "partial"), ("above" if above else "below")


def _qualifier_holds(ctx: ReasoningContext, c: ClauseConstraint) -> Optional[bool]:
    """Does the constraint's qualifier (e.g. exposure_condition=severe) hold for this document?"""
    if not c.qualifier:
        return True
    key, _, value = c.qualifier.partition("=")
    values = ctx.qualifiers.get(key)
    if not values:
        return None
    return any(v.lower() == value.lower() for v in values)


def _candidate_standards(ctx: ReasoningContext, req: StructuredRequirement) -> list[CorpusStandard]:
    """Standards to check a requirement against: those it cites plus its own top retrieval hit.

    Checking against every standard in the document would compare, say, a
    panel voltage with a cable's voltage grade.
    """
    ids: dict[str, None] = {}
    mapping = ctx.mapping_for(req.id)
    top = mapping.hits[0] if mapping and mapping.hits else None
    gate = current().detector_gate
    if top and top.confidence >= ctx.threshold:
        if not gate or (top.confidence >= GATE_CONFIDENCE and in_scope(ctx, req, top.standard_id)):
            ids[top.standard_id] = None
    for r in ctx.resolved.get(req.id, []):
        if r.standard_id:
            ids[r.standard_id] = None
    return [s for s in (standard_by_id(ctx, i) for i in ids) if s]


def _ambiguous(ctx: ReasoningContext, req: StructuredRequirement, standard_id: str, parameter: str, q: Quantity) -> bool:
    """v3 gate: a retrieval-only mapping does not raise a conflict when a close runner-up standard
    that also governs the parameter accepts the value (e.g. 90 °C conductor temperature: PVC vs XLPE cable)."""
    if not current().detector_gate:
        return False
    if any(r.standard_id == standard_id for r in ctx.resolved.get(req.id, [])):
        return False  # cited explicitly: the purchaser chose this standard
    mapping = ctx.mapping_for(req.id)
    if not mapping or not mapping.hits:
        return False
    top = mapping.hits[0].confidence
    for hit in mapping.hits[1:]:
        if hit.standard_id == standard_id or hit.confidence < top - 0.15:
            continue
        other = ctx.corpus.standard(hit.standard_id)
        for clause in other.clauses if other else []:
            for c in clause.constraints:
                if c.parameter == parameter and c.dimension == q.dimension and compare(q, c)[0] == "none":
                    return True
    return False


def check_constraints(ctx: ReasoningContext) -> list[ConstraintCheck]:
    checks: list[ConstraintCheck] = []
    for req in ctx.requirements:
        quantified = [a for a in req.attributes if a.quantity]
        if not quantified:
            continue
        for std in _candidate_standards(ctx, req):
            for clause in std.clauses:
                for constraint in clause.constraints:
                    for attr in quantified:
                        q = attr.quantity
                        if not q or attr.parameter != constraint.parameter or q.dimension != constraint.dimension:
                            continue
                        if _qualifier_holds(ctx, constraint) is not True:
                            continue
                        violation, side = compare(q, constraint)
                        if violation != "none" and _ambiguous(ctx, req, std.id, attr.parameter, q):
                            continue
                        checks.append(ConstraintCheck(req, q, attr.parameter, std, clause, constraint, violation, side))
    return checks


def constraint_conflict_findings(checks: list[ConstraintCheck]) -> list[ReasoningFinding]:
    seen: set[str] = set()
    out: list[ReasoningFinding] = []
    for check in checks:
        if check.violation == "none":
            continue
        key = f"{check.requirement.id}|{check.parameter}|{check.standard.id}"
        if key in seen:
            continue
        seen.add(key)
        req, q, std, clause, constraint = check.requirement, check.quantity, check.standard, check.clause, check.constraint
        param_label = label(check.parameter)
        stated = describe_quantity(q)
        limit = fmt_bound(constraint)
        special = bool(re.search(r"special|permissible|relax|derat", constraint.condition, re.I))
        partly = " for part of its range" if check.violation == "partial" else ""
        out.append(
            ReasoningFinding(
                id="",
                kind="conflicting",
                rule="constraint_conflict",
                parameter=check.parameter,
                title=f"Potential {param_label.lower()} conflict",
                severity="high" if check.violation == "disjoint" else "medium",
                requirement_id=req.id,
                requirement_text=req.text,
                standard_id=std.id,
                clause_id=clause.id,
                standard_label=clause_label(std, clause),
                reason=(
                    f"The requirement specifies {param_label.lower()} of {stated}, but {std.number} "
                    f"({clause.heading.lower()}) limits it to {limit} for {constraint.condition}. "
                    f"The stated value is {check.side} this limit{partly}."
                ),
                action=(
                    f"Align the value with {limit}, or declare it as a special condition and require documented "
                    "design basis and verification evidence from the manufacturer."
                    if special
                    else f"Revise the requirement to {limit} in accordance with {std.number}, or record the technical "
                    "justification for deviating from it."
                ),
                evidence=[
                    requirement_evidence(req),
                    clause_evidence(std, clause),
                    Evidence(
                        kind="constraint_check",
                        label="Interval check",
                        excerpt=(
                            f'{param_label}: requirement {stated} (from "{q.raw}") vs. {std.number} {limit} '
                            f"[{constraint.condition}] → "
                            f"{'entirely outside' if check.violation == 'disjoint' else 'partly outside'} "
                            f"the permitted range ({check.side})."
                        ),
                        requirement_id=req.id,
                        span=q.span,
                        standard_id=std.id,
                        clause_id=clause.id,
                    ),
                ],
                provenance=provenance(
                    "reasoning.conflicts",
                    "constraint",
                    0.9 if check.violation == "disjoint" else 0.75,
                    [
                        f'parameter {check.parameter} parsed from "{q.raw}"',
                        f"constraint from {clause.id}"
                        + (f" (applies because {constraint.qualifier})" if constraint.qualifier else ""),
                        f"violation {check.violation} ({check.side})",
                    ],
                ),
            )
        )
    return out


# Parameters that should have a single value across a specification. Voltage
# and current are excluded because specifications legitimately state several
# (supply vs. control circuits, different feeders).
SINGLE_VALUED = ["ambient_temperature", "frequency", "altitude", "exposure_condition"]


def intra_document_conflicts(ctx: ReasoningContext) -> list[ReasoningFinding]:
    out: list[ReasoningFinding] = []
    for parameter in SINGLE_VALUED:
        items = [(req, attr) for req, attr in document_attributes(ctx, parameter) if attr.quantity or attr.text]
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a_req, a_attr = items[i]
                b_req, b_attr = items[j]
                if a_req.id == b_req.id:
                    continue
                inconsistent = False
                a_desc = a_attr.text or ""
                b_desc = b_attr.text or ""
                qa, qb = a_attr.quantity, b_attr.quantity
                if qa and qb:
                    if qa.dimension != qb.dimension:
                        continue
                    a_desc, b_desc = describe_quantity(qa), describe_quantity(qb)
                    amin = qa.min if qa.min is not None else -math.inf
                    amax = qa.max if qa.max is not None else math.inf
                    bmin = qb.min if qb.min is not None else -math.inf
                    bmax = qb.max if qb.max is not None else math.inf
                    inconsistent = amax < bmin or bmax < amin
                elif a_attr.text and b_attr.text:
                    inconsistent = a_attr.text.lower() != b_attr.text.lower()
                if not inconsistent:
                    continue
                name = label(parameter).lower()
                out.append(
                    ReasoningFinding(
                        id="",
                        kind="conflicting",
                        rule="internal_inconsistency",
                        title=f"Inconsistent {name} within the specification",
                        severity="medium",
                        requirement_id=a_req.id,
                        requirement_text=f"{a_req.text} / {b_req.text}",
                        standard_id=None,
                        clause_id=None,
                        standard_label="Internal consistency check",
                        reason=(
                            f"Two requirements state different values for {name}: {a_desc} and {b_desc}. "
                            "Bidders cannot comply with both."
                        ),
                        action=f"State a single {name} for the whole specification and remove the other value.",
                        evidence=[
                            requirement_evidence(a_req, "First statement"),
                            requirement_evidence(b_req, "Second statement"),
                        ],
                        provenance=provenance(
                            "reasoning.conflicts", "constraint", 0.8, [f"{parameter} values {a_desc} vs {b_desc} do not overlap"]
                        ),
                    )
                )
    return out


def reference_edition_conflicts(ctx: ReasoningContext) -> list[ReasoningFinding]:
    """The same designation cited with two different editions."""
    by_standard: dict[str, list[tuple[StructuredRequirement, int, str]]] = {}
    for req in ctx.requirements:
        for r in ctx.resolved.get(req.id, []):
            if not r.standard_id or r.reference.year is None:
                continue
            by_standard.setdefault(r.standard_id, []).append((req, r.reference.year, r.reference.raw))
    out: list[ReasoningFinding] = []
    for standard_id, cites in by_standard.items():
        years = list(dict.fromkeys(year for _, year, _ in cites))
        if len(years) < 2:
            continue
        std = standard_by_id(ctx, standard_id)
        if not std:
            continue
        first_req = cites[0][0]
        out.append(
            ReasoningFinding(
                id="",
                kind="conflicting",
                rule="edition_conflict",
                title=f"Different editions of {std.designation} cited",
                severity="medium",
                requirement_id=first_req.id,
                requirement_text=" / ".join(req.text for req, _, _ in cites),
                standard_id=standard_id,
                clause_id=None,
                standard_label=std.number,
                reason=(
                    f"The specification cites {' and '.join(raw for _, _, raw in cites)}. "
                    "Requirements may differ between editions."
                ),
                action=f"Cite a single edition throughout — the corpus lists {std.number} as the {std.status} edition.",
                evidence=[requirement_evidence(req, f"Cites {raw}") for req, _, raw in cites],
                provenance=provenance(
                    "reasoning.conflicts", "rule", 0.9, [f"editions cited: {', '.join(str(y) for y in years)}"]
                ),
            )
        )
    return out
