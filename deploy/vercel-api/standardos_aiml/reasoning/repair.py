"""Repair generation.

Repairs are built from templates grounded in the finding's evidence (the
violated limit, the checklist wording, the replacement standard), so every
number and designation in a proposal is traceable. An optional LLM pass
(``standardos_aiml.llm_repair``) may rephrase the wording but is rejected if
it alters those facts. Repairs are proposals: they take effect only after a
reviewer accepts them.
"""

from __future__ import annotations

import re
from typing import Optional

from ..nlp.units import format_canonical
from ..provenance import fmt_num, provenance
from ..types import ReasoningFinding, RepairProposal
from .conflicts import ConstraintCheck
from .context import ReasoningContext, clause_by_id, standard_by_id

PLACEHOLDER_NOTE = "Values in [brackets] must be completed by the specifier."


def _with_citation(text: str, number: str) -> str:
    trimmed = re.sub(r"\.$", "", text.strip())
    return f"{trimmed}." if number in trimmed else f"{trimmed}, in accordance with {number}."


def _replace_first(text: str, old: str, new: str) -> str:
    return text.replace(old, new, 1)


def generate_repairs(
    ctx: ReasoningContext, findings: list[ReasoningFinding], checks: list[ConstraintCheck]
) -> list[RepairProposal]:
    out: list[RepairProposal] = []
    for f in findings:
        std = standard_by_id(ctx, f.standard_id)
        req = ctx.requirement(f.requirement_id)
        evidence_label = f.standard_label
        original = req.text if req else "Not stated in the specification."
        recommended: Optional[str] = None
        reason = ""

        if f.rule == "constraint_conflict":
            check = next(
                (
                    c
                    for c in checks
                    if c.requirement.id == f.requirement_id and c.clause.id == f.clause_id and c.violation != "none"
                ),
                None,
            )
            if check and req and std:
                constraint, quantity = check.constraint, check.quantity
                target = constraint.max if check.side == "above" else constraint.min
                if target is not None:
                    target_text = format_canonical(target, constraint.unit)
                    if check.parameter.endswith("_variation") and "±" in quantity.raw:
                        # Derived from "415 V ± 15 %": change only the tolerance.
                        new_text = _replace_first(
                            req.text,
                            quantity.raw,
                            re.sub(r"±\s*[\d.]+\s*%", f"±{fmt_num(target)} %", quantity.raw, count=1),
                        )
                    elif check.parameter == "concrete_grade":
                        new_text = _replace_first(req.text, quantity.raw, f"M{fmt_num(target)}")
                    elif quantity.comparator == "range" and constraint.min is not None and constraint.max is not None:
                        lo = format_canonical(
                            max(quantity.min if quantity.min is not None else constraint.min, constraint.min),
                            constraint.unit,
                        )
                        hi = format_canonical(
                            min(quantity.max if quantity.max is not None else constraint.max, constraint.max),
                            constraint.unit,
                        )
                        new_text = _replace_first(req.text, quantity.raw, f"{lo} to {hi}")
                    else:
                        new_text = _replace_first(req.text, quantity.raw, target_text)
                    recommended = _with_citation(new_text, std.number)
                    if re.search(r"special", constraint.condition, re.I):
                        recommended += (
                            " Any site condition beyond this shall be declared as a special service condition "
                            "and verified by the manufacturer."
                        )
                    reason = (
                        f"Brings the {check.parameter.replace('_', ' ')} within the limit of {std.number} "
                        f"({constraint.condition}) while keeping the rest of the requirement unchanged."
                    )
        elif f.rule in ("checklist_gap", "insufficient_specification"):
            item = next((i for i in std.checklist if i.parameter == f.parameter), None) if std else None
            if item and std:
                recommended = item.repair_template.replace("{standard}", std.number)
                if f.rule == "checklist_gap":
                    original = "Not stated in the specification."
                reason = f"{item.rationale} {PLACEHOLDER_NOTE if '[' in recommended else ''}".strip()
        elif f.rule == "dependency_gap":
            if std:
                is_test = f.title.startswith("Test method")
                recommended = (
                    f"Tests shall be carried out in accordance with {std.number}, and the test certificates shall be "
                    "submitted for acceptance."
                    if is_test
                    else f"The equipment shall also conform to {std.number} where applicable."
                )
                # A vague test requirement is rewritten; otherwise the clause is added.
                if not (req and req.vague):
                    original = "Not stated in the specification."
                reason = f.reason
        elif f.rule in ("superseded_reference", "superseded_edition"):
            cited = next((r for r in req.references if r.raw in f.title), None) if req and std and f.evidence else None
            if cited and req and std:
                # Parts that must be read with the replacement (IS/IEC 61439-2 with 61439-1).
                companions = [
                    s.number for s in (standard_by_id(ctx, r.from_id) for r in ctx.graph.incoming(std.id, ["REQUIRES"])) if s
                ]
                recommended = _replace_first(
                    req.text, cited.raw, f"{std.number} and {', '.join(companions)}" if companions else std.number
                )
                what = "withdrawn standard" if f.rule == "superseded_reference" else "superseded edition"
                reason = (
                    f"Replaces the {what} with {std.number}. Check that clause-level wording still matches the "
                    "current edition."
                )
        elif f.rule == "conformity_evidence_missing":
            if std:
                recommended = (
                    f"The supplier shall furnish evidence of conformity to {f.standard_label}: a valid BIS licence "
                    "(Standard Mark) for each offered product and/or type-test reports from an accredited laboratory, "
                    "as decided by the purchaser."
                )
                original = "Not stated in the specification."
                reason = (
                    "Makes conformity verifiable at bid evaluation. The choice between licence and type-test evidence "
                    "is a procurement decision left to the reviewer."
                )
        elif f.rule == "vague_requirement":
            if req:
                clause = clause_by_id(ctx, f.clause_id)
                per = ""
                if std:
                    per = f" per {std.number}" + (f" ({clause.heading})" if clause else "")
                recommended = (
                    f"{re.sub(r'\.$', '', req.text)} — [state the measurable value or acceptance criterion{per}]."
                )
                reason = "Qualitative wording cannot be verified. The reviewer must supply the measurable criterion."

        if not recommended:
            continue
        out.append(
            RepairProposal(
                id="",
                finding_id=f.id,
                original=original,
                recommended=re.sub(r"\s+", " ", recommended).strip(),
                evidence_label=evidence_label,
                reason=reason,
                provenance=provenance(
                    "repair.template",
                    "template",
                    f.provenance.confidence,
                    [f"template for rule {f.rule}", f"grounded in {evidence_label}"],
                ),
            )
        )
    return out
