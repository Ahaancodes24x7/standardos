"""Reasoning for test and inspection reports (``PipelineConfig.document_role == "report"``).

A specification states limits; a report states *results*. In a report the same
parameter usually appears twice — the value measured and the limit it is judged
against ("measured earth resistance 2.4 ohm … specified: not more than 1 ohm";
"Turbidity: acceptable limit 1 NTU; result 3.2 NTU"). This module:

1. gives every quantity a role — observed result or limit — from the nearest cue word
   before it in its sentence;
2. reports a nonconformity when an observed result lies outside a limit for the same
   parameter stated in the same sentence or elsewhere in the report (a bare guaranteed
   or declared value is read as a minimum or maximum from the parameter's polarity);
3. surfaces nonconformities the report itself declares ("Fail", "exceeds the
   specified …", "below the guaranteed …") that no numeric check already covers.

Limits taken from the standards themselves are checked by the constraint checker, on
observed results only (``observed_only``).
"""

from __future__ import annotations

import dataclasses
import math
import re
from typing import Optional

from ..nlp.parameters import PARAMETER_BY_KEY, parameter_label
from ..nlp.units import format_canonical
from ..provenance import provenance
from ..types import Attribute, Quantity, ReasoningFinding, StructuredRequirement
from .context import ReasoningContext, requirement_evidence

OBSERVED_CUE = re.compile(
    r"\b(measured|observed|results?|found|recorded|actual|reading|obtained|achieved|offered|declared)\b", re.I
)
LIMIT_CUE = re.compile(
    r"\b(specified|specification|guaranteed|required|requirement|limits?|permissible|acceptable|"
    r"not more than|not less than|not exceeding|max(imum)?\.?|min(imum)?\.?|shall|should)\b",
    re.I,
)
DECLARED_FAILURE = re.compile(
    r"\b(fail(ed|s)?|not complied|non[- ]?complian(ce|t)|does not (comply|conform|meet)|"
    r"exceeds? the (specified|guaranteed|permissible|acceptable|required|maximum)|"
    r"(is|are|was|were) below the (specified|guaranteed|required|minimum)|rejected|not acceptable|unsatisfactory|not satisfactory)\b",
    re.I,
)

# Which side of a bare guaranteed / declared value is acceptable.
POLARITY: dict[str, str] = {
    "efficiency": "min",
    "pump_head": "min",
    "flow_rate": "min",
    "short_circuit_rating": "min",
    "compressive_strength": "min",
    "noise_level": "max",
    "earth_resistance": "max",
    "conductor_temperature": "max",
    "turbidity": "max",
    "tds": "max",
    "fluoride": "max",
    "nitrate": "max",
    "chloride": "max",
    "arsenic": "max",
    "total_hardness": "max",
}
SAFETY = {"earth_resistance", "turbidity", "tds", "fluoride", "nitrate", "chloride", "arsenic", "total_hardness"}


def quantity_role(req: StructuredRequirement, q: Quantity) -> str:
    """'limit' or 'observed' for a quantity in a report sentence."""
    prefix = req.text[: max(0, q.span.start - req.span.start)]
    last = lambda rx: max((m.end() for m in rx.finditer(prefix)), default=-1)
    obs, lim = last(OBSERVED_CUE), last(LIMIT_CUE)
    if lim > obs:
        return "limit"
    if obs >= 0:
        return "observed"
    return "limit" if q.comparator in ("min", "max") else "observed"


def observed_only(ctx: ReasoningContext) -> ReasoningContext:
    """The context with limit quantities removed, so standard-limit checks judge results only."""
    reqs = [
        dataclasses.replace(
            r,
            attributes=[a for a in r.attributes if not (a.quantity and quantity_role(r, a.quantity) == "limit")],
        )
        for r in ctx.requirements
    ]
    return dataclasses.replace(ctx, requirements=reqs)


def _interval(q: Quantity, parameter: str) -> Optional[tuple[float, float]]:
    lo = q.min if q.min is not None else -math.inf
    hi = q.max if q.max is not None else math.inf
    if q.comparator in ("eq", "tolerance") and q.value is not None:
        side = POLARITY.get(parameter)
        if side == "min":
            return (q.value, math.inf)
        if side == "max":
            return (-math.inf, q.value)
        return None
    return (lo, hi)


def _fmt(value: float, q: Quantity) -> str:
    if q.unit == "mm" and abs(value) >= 1000:
        return f"{value / 1000:g} m"
    return format_canonical(value, q.unit)


def _citation(ctx: ReasoningContext, req: StructuredRequirement) -> Optional[str]:
    return next((r.standard_id for r in ctx.resolved.get(req.id, []) if r.standard_id), None)


def observation_findings(ctx: ReasoningContext) -> list[ReasoningFinding]:
    observed: list[tuple[StructuredRequirement, Attribute]] = []
    limits: dict[str, list[tuple[StructuredRequirement, Attribute]]] = {}
    for req in ctx.requirements:
        for a in req.attributes:
            if not a.quantity:
                continue
            if quantity_role(req, a.quantity) == "limit":
                limits.setdefault(a.parameter, []).append((req, a))
            else:
                observed.append((req, a))

    out: list[ReasoningFinding] = []
    seen: set[tuple[str, float | None]] = set()
    for req, a in observed:
        q = a.quantity
        assert q is not None
        candidates = [(r, l) for r, l in limits.get(a.parameter, []) if l.quantity and l.quantity.dimension == q.dimension]
        same = [(r, l) for r, l in candidates if r.id == req.id]
        for lim_req, lim in same or candidates:
            assert lim.quantity is not None
            bounds = _interval(lim.quantity, a.parameter)
            if not bounds:
                continue
            lo, hi = bounds
            v_lo = q.min if q.min is not None else q.value
            v_hi = q.max if q.max is not None else q.value
            if v_lo is None or v_hi is None:
                continue
            over = v_hi > hi + 1e-9
            under = v_lo < lo - 1e-9
            if not (over or under):
                continue
            key = (a.parameter, q.value)
            if key in seen:
                break
            seen.add(key)
            name = parameter_label(a.parameter)
            limit_value = hi if over else lo
            deviation = abs((v_hi if over else v_lo) - limit_value) / abs(limit_value) if limit_value else 1.0
            # Pump discharge and head are accepted within the test standard's tolerance band, so a
            # shortfall of 2 % or less is flagged for checking rather than as a failure.
            if a.parameter in SAFETY or deviation > 0.1:
                severity = "high"
            elif a.parameter in ("flow_rate", "pump_head") and deviation <= 0.02:
                severity = "low"
            else:
                severity = "medium"
            stated = _fmt(v_hi if over else v_lo, q)
            limit_text = f"{'at most' if over else 'at least'} {_fmt(limit_value, lim.quantity)}"
            std_id = _citation(ctx, lim_req) or _citation(ctx, req)
            std = ctx.corpus.standard(std_id) if std_id else None
            evidence = [requirement_evidence(req, "Result in the report")]
            if lim_req.id != req.id:
                evidence.append(requirement_evidence(lim_req, "Limit stated in the report"))
            tolerance = (
                " Check it against the acceptance tolerance of the test standard before rejecting."
                if severity == "low"
                else ""
            )
            out.append(
                ReasoningFinding(
                    id="",
                    kind="conflicting",
                    rule="result_nonconformity",
                    parameter=a.parameter,
                    title=f"{name} {stated} is {'above' if over else 'below'} the limit ({limit_text})",
                    severity=severity,
                    requirement_id=req.id,
                    requirement_text=req.text,
                    standard_id=std.id if std else None,
                    clause_id=None,
                    standard_label=std.number if std else "Limit stated in this report",
                    reason=(
                        f"The report records {name.lower()} of {stated}; the limit it is judged against is "
                        f"{limit_text}{f' ({std.number})' if std else ''}.{tolerance}"
                    ),
                    action=f"Treat as a nonconformity: obtain a corrective action and a repeat test for {name.lower()}.",
                    evidence=evidence,
                    provenance=provenance(
                        "reasoning.conflicts",
                        "constraint",
                        0.9,
                        [f"observed {stated} vs limit {limit_text}", f"limit from: {lim_req.text[:80]}"],
                    ),
                )
            )
            break

    flagged = {f.parameter for f in out if f.parameter}
    flagged_words = [parameter_label(p).lower() for p in flagged]
    for p in flagged:
        d = PARAMETER_BY_KEY.get(p)
        if d:
            flagged_words += [c for c in (*d.cues, *d.mention_cues) if len(c) > 3]
    for req in ctx.requirements:
        m = DECLARED_FAILURE.search(req.text)
        if not m:
            continue
        params = {a.parameter for a in req.attributes}
        text = req.text.lower()
        if params & flagged or any(w in text for w in flagged_words):
            continue
        out.append(
            ReasoningFinding(
                id="",
                kind="conflicting",
                rule="reported_nonconformity",
                parameter=next(iter(params), None),
                title="The report records a nonconformity",
                severity="high",
                requirement_id=req.id,
                requirement_text=req.text,
                standard_id=_citation(ctx, req),
                clause_id=None,
                standard_label="Stated in this report",
                reason=f'The report itself records a failed or non-conforming result ("{m.group(0)}").',
                action="Resolve the nonconformity (corrective action and re-test) before accepting the material or work.",
                evidence=[requirement_evidence(req, "Statement in the report")],
                provenance=provenance("reasoning.conflicts", "rule", 0.85, [f'declared failure cue "{m.group(0)}"']),
            )
        )
    return out


def reword_for_report(findings: list[ReasoningFinding]) -> list[ReasoningFinding]:
    """Constraint conflicts in a report are results outside a standard's limit, not specification conflicts."""
    for f in findings:
        if f.rule == "constraint_conflict":
            name = parameter_label(f.parameter or "") if f.parameter else "Result"
            f.title = f"{name} outside the {f.standard_label.split(' · ')[0]} limit"
            f.reason = f.reason.replace("The requirement specifies", "The report records")
            f.action = "Treat as a nonconformity: obtain a corrective action and a repeat test."
    return findings
