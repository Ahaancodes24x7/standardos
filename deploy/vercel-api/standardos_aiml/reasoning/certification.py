"""Certification reasoning.

When product standards with a BIS certification route apply, the
specification should say how conformity will be demonstrated. Whether the
Standard Mark is legally mandatory depends on the Quality Control Orders in
force, which the corpus does not track, so the finding asks the purchaser to
decide rather than asserting it. One finding covers all such standards in the
document, with evidence for each.
"""

from __future__ import annotations

import dataclasses
import re

from ..config import current
from ..nlp.entities import extract_product_terms
from ..provenance import provenance
from ..types import CorpusStandard, Evidence, ReasoningFinding
from .context import (
    ReasoningContext,
    clause_evidence,
    document_attributes,
    has_value,
    requirement_evidence,
    standard_by_id,
    strong_applicable,
)


# v3.1: evidence about a sample, a source or a material under test ("water samples shall be
# tested at a NABL laboratory", "test reports for every source") is not evidence of product
# conformity, even though it names no product.
_TEST_SUBJECT = re.compile(r"\b(samples?|sources?|specimens?|cubes?|water|soil|concrete|mix)\b", re.I)


def _covered(ctx: ReasoningContext, std: CorpusStandard, evidence_reqs: list) -> bool:
    """v3: does some conformity-evidence requirement cover this product standard?

    Covered when an evidence requirement cites it, maps to it, names a product the
    standard covers, or names no product at all ("all equipment shall be ISI marked").
    """
    for req in evidence_reqs:
        if any(r.standard_id == std.id for r in ctx.resolved.get(req.id, [])):
            return True
        m = ctx.mapping_for(req.id)
        if m and m.hits and m.hits[0].standard_id == std.id:
            return True
        terms = req.terms or extract_product_terms(req.text)
        if not terms:
            if current().reasoning_v31 and _TEST_SUBJECT.search(req.text):
                continue
            return True
        if ctx.index is not None and any(ctx.index.matches_product(std, t) for t in terms):
            return True
    return False


def certification_findings(ctx: ReasoningContext) -> list[ReasoningFinding]:
    evidence_reqs = [req for req, attr in document_attributes(ctx, "conformity_evidence") if has_value(attr)]
    scoped = current().certification_scope
    if evidence_reqs and not scoped:
        return []
    products: list[tuple[CorpusStandard, list[str]]] = []
    for app in strong_applicable(ctx):
        std = standard_by_id(ctx, app.standard_id)
        # A cited superseded product standard still means the product needs
        # conformity evidence — against the standard that replaced it.
        if std and std.status in ("superseded", "withdrawn"):
            latest = ctx.graph.latest_replacement(std.id)
            std = standard_by_id(ctx, latest.id) if latest else None
        if (
            std
            and std.kind == "product"
            and std.certification.scheme
            and not any(p.id == std.id for p, _ in products)
            and not (scoped and _covered(ctx, std, evidence_reqs))
        ):
            products.append((std, app.requirement_ids))
    if not products:
        return []

    numbers = [p.number for p, _ in products]
    evidence: list[Evidence] = []
    for std, requirement_ids in products:
        anchor = next((r for r in ctx.requirements if r.id in requirement_ids), None)
        if anchor:
            evidence.append(requirement_evidence(anchor, f"Why {std.number} applies"))
        evidence.append(
            dataclasses.replace(
                clause_evidence(std, std.clauses[0] if std.clauses else None),
                label=f"{std.number} · certification route",
                excerpt=f"{std.certification.scheme}. {std.scope}",
            )
        )
    first_std, first_ids = products[0]
    anchor = next((r for r in ctx.requirements if r.id in first_ids), None)
    listing = f"{', '.join(numbers[:-1])} and {numbers[-1]}" if len(numbers) > 1 else numbers[0]
    plural = len(numbers) > 1

    return [
        ReasoningFinding(
            id="",
            kind="certification",
            rule="conformity_evidence_missing",
            parameter="conformity_evidence",
            title=(
                f"Conformity evidence is not specified for {len(numbers)} product standards"
                if plural
                else f"Conformity evidence for {listing} is not specified"
            ),
            severity="medium",
            requirement_id=anchor.id if anchor else None,
            requirement_text=anchor.text if anchor else f"Specification invokes {listing}",
            standard_id=first_std.id,
            clause_id=None,
            standard_label=listing,
            reason=(
                f"{listing} {'are product standards with' if plural else 'is a product standard with'} a BIS "
                "certification route, but the specification does not state how conformity is to be demonstrated, "
                "so bids cannot be evaluated consistently."
            ),
            action=(
                f"Specify the conformity evidence required for {listing}: a valid BIS licence (Standard Mark) for the "
                "offered product and/or type-test reports from an accredited laboratory. Confirm whether a Quality "
                "Control Order makes certification mandatory."
            ),
            evidence=evidence,
            provenance=provenance(
                "reasoning.certification",
                "rule",
                0.7,
                [
                    *[f"{p.number}: kind=product, certification scheme recorded" for p, _ in products],
                    "no requirement states ISI mark, BIS licence, type-test report or test certificate",
                ],
            ),
        )
    ]
