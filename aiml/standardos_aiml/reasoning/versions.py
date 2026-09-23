"""Version/change reasoning for cited standards.

* superseded_reference — the cited standard itself has been replaced
* superseded_edition   — an older edition of a current standard is cited
* newer_edition        — the cited edition is newer than the corpus (corpus lag)
* amendment_check      — the cited standard has amendments to verify
"""

from __future__ import annotations

from ..provenance import provenance
from ..types import Evidence, ReasoningFinding
from .context import ReasoningContext, requirement_evidence, standard_by_id


def companion_parts(ctx: ReasoningContext, standard_id: str) -> str:
    """Parts that must be read with a replacement (e.g. IS/IEC 61439-2 with 61439-1), from REQUIRES edges."""
    parts = [s.number for s in (standard_by_id(ctx, r.from_id) for r in ctx.graph.incoming(standard_id, ["REQUIRES"])) if s]
    return f" and the applicable part read with it (e.g. {', '.join(parts)})" if parts else ""


def version_findings(ctx: ReasoningContext) -> list[ReasoningFinding]:
    out: list[ReasoningFinding] = []
    seen: set[str] = set()
    for req in ctx.requirements:
        for r in ctx.resolved.get(req.id, []):
            if not r.standard_id:
                continue
            std = standard_by_id(ctx, r.standard_id)
            if not std:
                continue
            key = f"{req.id}|{std.id}"
            if key in seen:
                continue
            seen.add(key)
            events = [e for e in ctx.corpus.events if e.standard_id == std.id]
            version_evidence = [
                Evidence(
                    kind="version_record",
                    label=f"{e.kind}{f' · {e.date}' if e.date else ' · date not recorded'}",
                    excerpt=e.summary,
                    standard_id=std.id,
                )
                for e in events
            ]

            if std.status in ("superseded", "withdrawn"):
                latest = ctx.graph.latest_replacement(std.id)
                replacement_id = latest.id if latest else next((e.replaced_by_id for e in events if e.replaced_by_id), None)
                replacement = standard_by_id(ctx, replacement_id)
                path_evidence: list[Evidence] = []
                if latest:
                    steps = []
                    for p in latest.path:
                        frm, to = standard_by_id(ctx, p.from_id), standard_by_id(ctx, p.to_id)
                        steps.append(f"{frm.number if frm else None} SUPERSEDES {to.number if to else None}")
                    path_evidence.append(
                        Evidence(
                            kind="graph_path",
                            label="Supersession path",
                            excerpt="; ".join(steps),
                            relationship_ids=[p.id for p in latest.path],
                        )
                    )
                replaced = f" and is replaced by {replacement.number} ({replacement.title})" if replacement else ""
                out.append(
                    ReasoningFinding(
                        id="",
                        kind="outdated",
                        rule="superseded_reference",
                        title=f"{r.reference.raw} has been {std.status}",
                        severity="high",
                        requirement_id=req.id,
                        requirement_text=req.text,
                        standard_id=replacement.id if replacement else std.id,
                        clause_id=None,
                        standard_label=f"{std.number} → {replacement.number}" if replacement else std.number,
                        reason=(
                            f"{std.number} is recorded as {std.status}{replaced}. "
                            "Bids evaluated against a withdrawn standard may not meet current requirements."
                        ),
                        action=(
                            f"Replace {r.reference.raw} with {replacement.number}{companion_parts(ctx, replacement.id)}."
                            if replacement
                            else f"Identify and cite the standard that replaced {std.number}."
                        ),
                        evidence=[requirement_evidence(req), *version_evidence, *path_evidence],
                        provenance=provenance(
                            "reasoning.versions",
                            "graph",
                            0.85 * r.provenance.confidence,
                            [*r.provenance.signals, f"status {std.status}"],
                        ),
                    )
                )
                continue

            if r.edition == "older":
                replacement = standard_by_id(ctx, r.replaced_by_id or std.id) or std
                out.append(
                    ReasoningFinding(
                        id="",
                        kind="outdated",
                        rule="superseded_edition",
                        title=f"Superseded edition {r.reference.raw} cited",
                        severity="medium",
                        requirement_id=req.id,
                        requirement_text=req.text,
                        standard_id=replacement.id,
                        clause_id=None,
                        standard_label=replacement.number,
                        reason=(
                            f"The requirement cites the {r.reference.year} edition, but the current edition in the "
                            f"corpus is {replacement.number}. Clause numbers and technical requirements may have changed."
                        ),
                        action=f"Cite {replacement.number} and check that the requirement still matches the revised clauses.",
                        evidence=[requirement_evidence(req), *version_evidence],
                        provenance=provenance(
                            "reasoning.versions", "rule", 0.85 * r.provenance.confidence, r.provenance.signals
                        ),
                    )
                )
                continue

            if r.edition == "newer":
                out.append(
                    ReasoningFinding(
                        id="",
                        kind="outdated",
                        rule="newer_edition",
                        title=f"Cited edition of {std.designation} is not in the corpus",
                        severity="low",
                        requirement_id=req.id,
                        requirement_text=req.text,
                        standard_id=std.id,
                        clause_id=None,
                        standard_label=std.number,
                        reason=(
                            f"The requirement cites the {r.reference.year} edition, newer than the {std.year} edition "
                            "held in the StandardOS corpus. Analysis for this standard used the older edition."
                        ),
                        action="Update the standards corpus with the cited edition, then re-run the analysis.",
                        evidence=[requirement_evidence(req)],
                        provenance=provenance("reasoning.versions", "rule", 0.6, r.provenance.signals),
                    )
                )
                continue

            amendment = next((e for e in events if e.kind == "amendment"), None)
            if amendment:
                out.append(
                    ReasoningFinding(
                        id="",
                        kind="outdated",
                        rule="amendment_check",
                        title=f"Amendments to {std.number} should be confirmed",
                        severity="low",
                        requirement_id=req.id,
                        requirement_text=req.text,
                        standard_id=std.id,
                        clause_id=None,
                        standard_label=std.number,
                        reason=amendment.summary,
                        action=f'State "{std.number} including all amendments" or name the amendment the requirement relies on.',
                        evidence=[requirement_evidence(req), *version_evidence],
                        provenance=provenance("reasoning.versions", "rule", 0.6, [f"amendment record {amendment.id}"]),
                    )
                )
    return out
