"""Dependency-aware reasoning.

If the specification invokes standard A and A REQUIRES / is TESTED_BY standard
B, check that the specification addresses B — by citing it (or its current
replacement), by a requirement that maps to it, or by a test requirement
naming it.
"""

from __future__ import annotations

import re
from typing import Optional

from ..provenance import fmt_num, provenance
from ..types import Evidence, ReasoningFinding, StructuredRequirement
from ..config import current
from .context import (
    ReasoningContext,
    cited_ids,
    clause_by_id,
    clause_evidence,
    clause_label,
    requirement_evidence,
    standard_by_id,
    strong_applicable,
)

MIN_EDGE_CONFIDENCE = 0.7


def dependency_gaps(ctx: ReasoningContext, consumed: set[str]) -> list[ReasoningFinding]:
    mode = current().dependency_mode
    if mode == "dag" and ctx.dag is not None:
        return _dag_dependency_gaps(ctx, consumed)
    out: list[ReasoningFinding] = []
    addressed = _addressed_standards(ctx) if mode == "legacy" else _cited_and_relatives(ctx)
    reported: set[str] = set()

    for app in strong_applicable(ctx):
        a = standard_by_id(ctx, app.standard_id)
        if not a:
            continue
        # v3.1: "you invoked A, which needs B" presumes the purchaser invoked A. A standard
        # reached only by retrieval (a starter panel mapped to IS/IEC 61439-2) imposes no dependencies.
        if current().reasoning_v31 and not app.explicit:
            continue
        # A product standard's normative references (cable → conductor standard,
        # pumpset → motor standard) bind the manufacturer, not the purchaser, so
        # only its TESTED_BY edges (acceptance testing) are procurement concerns.
        types = ["TESTED_BY"] if a.kind == "product" else ["REQUIRES", "TESTED_BY"]
        # Low-confidence (unverified) edges are shown in the graph but do not raise findings.
        for rel in [r for r in ctx.graph.outgoing(a.id, types) if r.confidence >= MIN_EDGE_CONFIDENCE]:
            replacement = ctx.graph.latest_replacement(rel.to_id)
            target_id = replacement.id if replacement else rel.to_id
            if rel.to_id in addressed or target_id in addressed or target_id in reported:
                continue
            b = standard_by_id(ctx, target_id)
            cited = standard_by_id(ctx, rel.to_id)
            if not b or not cited:
                continue
            reported.add(target_id)

            # Attach the finding to the requirement it should repair: a vague test
            # requirement for TESTED_BY, otherwise the requirement that invoked A.
            invoking = [r for r in ctx.requirements if r.id in app.requirement_ids]
            target: Optional[StructuredRequirement] = None
            if rel.type == "TESTED_BY":
                target = next(
                    (
                        r
                        for r in ctx.requirements
                        if r.category == "testing"
                        and (r.vague or r.id in app.requirement_ids)
                        and r.id not in consumed
                    ),
                    None,
                )
            if target is None and invoking:
                target = invoking[0]
            if target and target.vague:
                consumed.add(target.id)

            clause = clause_by_id(ctx, rel.clause_id)
            superseded = f" —SUPERSEDED_BY→ {b.number}" if replacement else ""
            path = Evidence(
                kind="graph_path",
                label="Dependency path",
                excerpt=(
                    f"{a.number} —{rel.type}→ {cited.number}{superseded} "
                    f"({rel.method} relationship, confidence {fmt_num(rel.confidence)})"
                ),
                standard_id=b.id,
                relationship_ids=[rel.id, *([p.id for p in replacement.path] if replacement else [])],
            )
            evidence: list[Evidence] = [path, clause_evidence(a, clause)]
            if target:
                evidence.insert(
                    0,
                    requirement_evidence(
                        target,
                        "Test requirement"
                        if rel.type == "TESTED_BY" and target.category == "testing"
                        else f"Requirement invoking {a.number}",
                    ),
                )

            is_test = rel.type == "TESTED_BY"
            basis = "cited" if app.explicit else f"retrieval confidence {app.confidence:.2f}"
            if is_test:
                revised = f", now revised as {b.number}" if replacement else ""
                reason = (
                    f"{a.number} relies on {cited.number} for testing{revised}, but the specification does not "
                    "name the test method, so acceptance tests cannot be enforced."
                )
            else:
                now = f" (now {b.number})" if replacement else ""
                note = re.sub(r"\.$", "", rel.note)
                reason = (
                    f"{a.number} requires {cited.number}{now} ({note}). "
                    "The specification does not cite it or state an equivalent requirement."
                )
            out.append(
                ReasoningFinding(
                    id="",
                    kind="missing",
                    rule="dependency_gap",
                    title=(
                        f"Test method {b.number} is not specified"
                        if is_test
                        else f"{a.designation} depends on {b.designation}, which is not addressed"
                    ),
                    severity="medium",
                    requirement_id=target.id if target else None,
                    requirement_text=target.text if target else f"Specification invokes {a.number}",
                    standard_id=b.id,
                    clause_id=clause.id if clause else None,
                    standard_label=f"{clause_label(a, clause)} → {b.number}",
                    reason=reason,
                    action=(
                        f"Require tests to be carried out in accordance with {b.number} and the test certificates "
                        "to be submitted."
                        if is_test
                        else f"Add a requirement to conform to {b.number} where it applies."
                    ),
                    evidence=evidence,
                    provenance=provenance(
                        "reasoning.dependencies",
                        "graph",
                        min(0.85, rel.confidence),
                        [
                            f"{a.number} applies ({basis})",
                            f"graph edge {rel.id} {rel.type}",
                            f"followed supersession to {b.number}" if replacement else "no supersession on target",
                            "target not cited, not retrieved, and not named in a test requirement",
                        ],
                    ),
                )
            )
    return out


def _cited_and_relatives(ctx: ReasoningContext) -> set[str]:
    """v3: a dependency is addressed only when the document *cites* it (or its predecessor/replacement).

    2.1 also counted any standard retrieved at ≥ 0.5 for some requirement, which
    hid missing citations (audit: heldout t1, tenders b1).
    """
    ids = set(cited_ids(ctx))
    for sid in list(ids):
        for rel in ctx.graph.outgoing(sid, ["SUPERSEDES"]):
            ids.add(rel.to_id)
        latest = ctx.graph.latest_replacement(sid)
        if latest:
            ids.add(latest.id)
    return ids


def _dag_dependency_gaps(ctx: ReasoningContext, consumed: set[str]) -> list[ReasoningFinding]:
    """Dependency reasoning over the normative DAG.

    For each applicable standard, walk its transitive normative closure (product
    standards: TESTED_BY on the first hop). A dependency is reported only when it
    is not addressed and every intermediate standard on its path *is* addressed —
    i.e. the nearest missing obligation, not everything downstream of it.
    """
    dag = ctx.dag
    addressed = {dag.canon(i) for i in _cited_and_relatives(ctx)}
    out: list[ReasoningFinding] = []
    reported: set[str] = set()
    for app in strong_applicable(ctx):
        a = standard_by_id(ctx, app.standard_id)
        if not a:
            continue
        if current().reasoning_v31 and not app.explicit:
            continue
        first = ["TESTED_BY"] if a.kind == "product" else ["REQUIRES", "TESTED_BY"]
        for target, reach in sorted(dag.closure(a.id, first).items(), key=lambda kv: kv[1].depth):
            if target in addressed or target in reported:
                continue
            if any(e.source not in addressed and e.source != dag.canon(a.id) for e in reach.path[1:]):
                continue  # an intermediate obligation is itself missing; report that one instead
            b = standard_by_id(ctx, target)
            if not b:
                continue
            reported.add(target)
            rel = reach.path[-1].relationship
            is_test = reach.path[-1].type == "TESTED_BY"
            invoking = [r for r in ctx.requirements if r.id in app.requirement_ids]
            req_target = None
            if is_test:
                req_target = next(
                    (r for r in ctx.requirements if r.category == "testing" and (r.vague or r.id in app.requirement_ids) and r.id not in consumed),
                    None,
                )
            req_target = req_target or (invoking[0] if invoking else None)
            chain = " → ".join([a.number, *[(standard_by_id(ctx, e.target).number if standard_by_id(ctx, e.target) else e.target) for e in reach.path]])
            path_ev = Evidence(
                kind="graph_path",
                label="Normative dependency path (DAG)",
                excerpt=f"{chain} ({reach.depth} hop{'s' if reach.depth > 1 else ''}; supersessions contracted)",
                standard_id=b.id,
                relationship_ids=[e.relationship.id for e in reach.path],
            )
            evidence: list[Evidence] = [path_ev, clause_evidence(a, clause_by_id(ctx, rel.clause_id))]
            if req_target:
                evidence.insert(0, requirement_evidence(req_target, "Test requirement" if is_test else f"Requirement invoking {a.number}"))
            out.append(
                ReasoningFinding(
                    id="",
                    kind="missing",
                    rule="dependency_gap",
                    title=f"Test method {b.number} is not specified" if is_test else f"{a.designation} depends on {b.designation}, which is not addressed",
                    severity="medium",
                    requirement_id=req_target.id if req_target else None,
                    requirement_text=req_target.text if req_target else f"Specification invokes {a.number}",
                    standard_id=b.id,
                    clause_id=rel.clause_id,
                    standard_label=f"{a.number} → {b.number}",
                    reason=(
                        f"{a.number} relies on {b.number} for testing, but the specification does not name the test method."
                        if is_test
                        else f"{a.number} requires {b.number} (via {chain}). The specification does not cite it."
                    ),
                    action=(
                        f"Require tests to be carried out in accordance with {b.number} and the test certificates to be submitted."
                        if is_test
                        else f"Add a requirement to conform to {b.number} where it applies."
                    ),
                    evidence=evidence,
                    provenance=provenance(
                        "reasoning.dependencies",
                        "graph",
                        min(0.85, min(e.relationship.confidence for e in reach.path)),
                        [f"{a.number} applies", f"DAG path depth {reach.depth}", "nearest missing obligation on the path"],
                    ),
                )
            )
    return out


def _addressed_standards(ctx: ReasoningContext) -> set[str]:
    """Standards the document addresses: cited explicitly or confidently retrieved for some requirement."""
    ids: set[str] = set()
    for req in ctx.requirements:
        for r in ctx.resolved.get(req.id, []):
            if r.standard_id:
                ids.add(r.standard_id)
    for m in ctx.mappings:
        top = m.hits[0] if m.hits else None
        if top and top.confidence >= 0.5:
            ids.add(top.standard_id)
    # Citing a replacement addresses the edition it replaces, and vice versa.
    for standard_id in list(ids):
        for rel in ctx.graph.outgoing(standard_id, ["SUPERSEDES"]):
            ids.add(rel.to_id)
        latest = ctx.graph.latest_replacement(standard_id)
        if latest:
            ids.add(latest.id)
    return ids
