"""Optional LLM copy-editing of template repairs.

Why an LLM here and nowhere else: every detection in StandardOS is
deterministic and evaluated; the one place where language quality matters
more than recall is the wording of a proposed specification clause. Template
text is correct but stilted; an LLM can make it read like specification prose.
Each rewrite is then checked by ``validate_rewrite`` and discarded if any
number, designation or placeholder changed, so the LLM cannot add or alter
technical content.

Off by default: it sends specification text to an external API and costs money
per analysis. Enable with STANDARDOS_LLM_REPAIR=on (credentials are resolved by
the SDK from ANTHROPIC_API_KEY or an ``ant auth login`` profile).
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os

from .reasoning.repair_validate import validate_rewrite
from .types import RepairProposal
from .version import COMPONENT_VERSIONS

log = logging.getLogger(__name__)

REPAIR_MODEL = "claude-opus-5"

SYSTEM = """You copy-edit proposed clauses for Indian public-procurement technical specifications.
Rewrite each "recommended" clause so it reads as clear, formal specification language ("shall" statements).
Rules:
- Keep every number, unit, standard designation (e.g. "IS 3043:2018") and bracketed placeholder (e.g. "[value]") exactly as written.
- Do not add requirements, numbers, standards or conditions that are not in the input.
- Keep the clause about the same length. If it already reads well, return it unchanged."""

SCHEMA = {
    "type": "object",
    "properties": {
        "repairs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "recommended": {"type": "string"}},
                "required": ["id", "recommended"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["repairs"],
    "additionalProperties": False,
}


def llm_repair_enabled() -> bool:
    return os.environ.get("STANDARDOS_LLM_REPAIR") == "on"


def polish_repairs(repairs: list[RepairProposal]) -> list[RepairProposal]:
    if not llm_repair_enabled() or not repairs:
        return repairs
    import anthropic

    client = anthropic.Anthropic(timeout=60.0, max_retries=1)
    payload = {
        "repairs": [
            {"id": r.id, "original": r.original, "recommended": r.recommended, "reason": r.reason} for r in repairs
        ]
    }
    try:
        response = client.beta.messages.create(
            model=REPAIR_MODEL,
            max_tokens=8000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            system=SYSTEM,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
    except anthropic.APIStatusError as exc:
        log.warning("[repair-llm] API error %s: %s", exc.status_code, exc.message)
        return repairs
    except anthropic.APIConnectionError as exc:
        log.warning("[repair-llm] connection failed; keeping template repairs: %s", exc)
        return repairs
    if response.stop_reason in ("refusal", "max_tokens"):
        log.warning("[repair-llm] skipped: stop_reason=%s", response.stop_reason)
        return repairs
    text = "".join(block.text for block in response.content if block.type == "text")
    try:
        rewrites = {r["id"]: r["recommended"] for r in json.loads(text)["repairs"]}
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        log.warning("[repair-llm] unparseable response; keeping template repairs: %s", exc)
        return repairs

    out: list[RepairProposal] = []
    for repair in repairs:
        rewrite = rewrites.get(repair.id)
        if not rewrite or rewrite == repair.recommended:
            out.append(repair)
            continue
        check = validate_rewrite(repair.recommended, rewrite)
        prov = repair.provenance
        if not check.ok:
            signals = [*prov.signals, f"LLM rewrite rejected ({check.reason}); template kept"]
            out.append(dataclasses.replace(repair, provenance=dataclasses.replace(prov, signals=signals)))
            continue
        out.append(
            dataclasses.replace(
                repair,
                recommended=rewrite,
                provenance=dataclasses.replace(
                    prov,
                    component="repair.llm",
                    component_version=COMPONENT_VERSIONS["repair.llm"],
                    method="llm",
                    model=REPAIR_MODEL,
                    signals=[
                        *prov.signals,
                        "wording edited by LLM; numbers, references and placeholders verified unchanged",
                        f"template: {repair.recommended}",
                    ],
                ),
            )
        )
    return out
