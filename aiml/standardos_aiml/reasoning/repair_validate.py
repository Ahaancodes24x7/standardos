"""Guard for LLM-rephrased repairs.

A rewrite is accepted only if it keeps every fact of the template — numbers,
standard designations and [placeholders] — and introduces none. This makes the
LLM a copy-editor, not a source of technical content.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from ..nlp.entities import extract_standard_references

NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
PLACEHOLDER_RE = re.compile(r"\[[^\]]+\]")


def _numbers(text: str) -> list[str]:
    return [n.replace(",", ".", 1) for n in NUMBER_RE.findall(PLACEHOLDER_RE.sub(" ", text))]


def _designations(text: str) -> set[str]:
    return {f"{r.designation}{f':{r.year}' if r.year else ''}" for r in extract_standard_references(text)}


@dataclass
class RewriteCheck:
    ok: bool
    reason: Optional[str] = None


def validate_rewrite(template: str, rewrite: str) -> RewriteCheck:
    if not rewrite.strip():
        return RewriteCheck(False, "empty rewrite")
    if len(rewrite) > len(template) * 2 + 80:
        return RewriteCheck(False, "rewrite is much longer than the template")

    t_nums = Counter(_numbers(template))
    r_nums = Counter(_numbers(rewrite))
    for n, count in t_nums.items():
        if r_nums.get(n, 0) < count:
            return RewriteCheck(False, f"number {n} was dropped")
    for n in r_nums:
        if n not in t_nums:
            return RewriteCheck(False, f"number {n} was introduced")

    t_refs, r_refs = _designations(template), _designations(rewrite)
    for r in sorted(t_refs):
        if r not in r_refs:
            return RewriteCheck(False, f"reference {r} was dropped or changed")
    for r in sorted(r_refs):
        if r not in t_refs:
            return RewriteCheck(False, f"reference {r} was introduced")

    t_ph = len(PLACEHOLDER_RE.findall(template))
    r_ph = len(PLACEHOLDER_RE.findall(rewrite))
    if t_ph != r_ph:
        return RewriteCheck(False, f"placeholder count changed ({t_ph} → {r_ph})")
    return RewriteCheck(True)
