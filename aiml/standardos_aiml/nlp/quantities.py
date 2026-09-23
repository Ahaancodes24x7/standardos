"""Numeric quantity extraction with canonical units, ranges, tolerances and comparators."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional

from ..types import Quantity, TextSpan
from .parameters import DEFAULT_PARAMETER_FOR_DIMENSION, PARAMETERS
from .units import UNIT_PATTERN, lookup_unit, to_canonical

NUM = r"[-]?\d+(?:,\d{3})*(?:\.\d+)?"

# number [unit] [(to|-|and) number] unit [± tol [unit]]
QUANTITY_RE = re.compile(
    rf"(?P<pm>±\s*)?(?P<a>{NUM})(?:\s*(?:(?P<ua>{UNIT_PATTERN})(?![A-Za-z0-9²³]))?\s*(?P<sep>to|–|—|-|and)\s*(?P<b>{NUM}))?"
    rf"\s*(?P<u>{UNIT_PATTERN})(?![A-Za-z0-9²³])(?:\s*(?:±|\+/-|\+-)\s*(?P<tol>\d+(?:\.\d+)?)\s*(?P<tolu>%|{UNIT_PATTERN})?)?"
)

PH_RE = re.compile(r"\bpH\b[^0-9.;]{0,45}?(?P<a>\d{1,2}(?:\.\d+)?)(?:\s*(?:to|–|-|and)\s*(?P<b>\d{1,2}(?:\.\d+)?))?")
WC_RE = re.compile(
    r"\b(?:free\s+)?(?:water[\s-]*cement\s+ratio|w\s*/\s*c\s+ratio)[^\d.]{0,40}?(?P<a>0?\.\d+)", re.I
)

MAX_PREFIX = re.compile(
    r"(?:not\s+exceeding|shall\s+not\s+exceed|not\s+to\s+exceed|not\s+more\s+than|no\s+more\s+than|maximum(?:\s+of)?"
    r"|max\.?(?:\s+of)?|up\s*to|upto|≤|<=|less\s+than|below|within|limited\s+to)\s*$",
    re.I,
)
MIN_PREFIX = re.compile(
    r"(?:not\s+less\s+than|no\s+less\s+than|minimum(?:\s+of)?|min\.?(?:\s+of)?|at\s+least|≥|>=|not\s+below"
    r"|more\s+than|greater\s+than|in\s+excess\s+of|above)\s*$",
    re.I,
)
MAX_SUFFIX = re.compile(r"^\s*(?:\(\s*max(?:imum|\.)?\s*\)|max(?:imum|\.)?\b|or\s+less\b|and\s+below\b)", re.I)
MIN_SUFFIX = re.compile(
    r"^\s*(?:\(\s*min(?:imum|\.)?\s*\)|min(?:imum|\.)?\b|or\s+more\b|and\s+above\b|or\s+above\b|or\s+higher\b)", re.I
)
BETWEEN_PREFIX = re.compile(r"(?:between|from|range\s+of|ranging\s+from)\s*$", re.I)


def _parse_num(value: str) -> float:
    return float(value.replace(",", ""))


def _tidy(value: float) -> float:
    return float(f"{value:.10g}") if math.isfinite(value) else value


def _comparator_for(text: str, start: int, end: int) -> Optional[str]:
    before = text[max(0, start - 40) : start]
    after = text[end : end + 20]
    # "not less than" contains "less than": the longer (more specific) match wins.
    mx = MAX_PREFIX.search(before)
    mn = MIN_PREFIX.search(before)
    max_len = len(mx.group(0)) if mx else 0
    min_len = len(mn.group(0)) if mn else 0
    if max_len or min_len:
        return "max" if max_len > min_len else "min"
    if MAX_SUFFIX.match(after):
        return "max"
    if MIN_SUFFIX.match(after):
        return "min"
    return None


def extract_quantities(text: str, base: int = 0) -> list[Quantity]:
    """Extract numeric quantities from ``text``.

    Offsets in the returned spans are relative to ``text`` plus ``base``, so
    callers can pass a sentence and its position in the document.
    """
    out: list[Quantity] = []
    taken: list[tuple[int, int]] = []

    def overlaps(s: int, e: int) -> bool:
        return any(s < b and e > a for a, b in taken)

    for m in PH_RE.finditer(text):
        a = float(m.group("a"))
        b = float(m.group("b")) if m.group("b") is not None else None
        if not (0 <= a <= 14) or (b is not None and not (0 <= b <= 14)):
            continue
        start, end = m.start(), m.end()
        taken.append((start, end))
        cmp = _comparator_for(text, start, end) if b is None else None
        out.append(
            Quantity(
                raw=m.group(0).strip(),
                span=TextSpan(base + start, base + end),
                value=a if b is None else None,
                min=(None if cmp == "max" else a) if b is None else min(a, b),
                max=(None if cmp == "min" else a) if b is None else max(a, b),
                unit="pH",
                dimension="ph",
                comparator="eq" if b is None else "range",
                tolerance=None,
            )
        )

    for m in WC_RE.finditer(text):
        value = float(m.group("a"))
        start, end = m.start(), m.end()
        taken.append((start, end))
        out.append(
            Quantity(
                raw=m.group(0).strip(),
                span=TextSpan(base + start, base + end),
                value=value,
                min=None,
                max=value,
                unit="ratio",
                dimension="ratio",
                comparator="max",
                tolerance=None,
            )
        )

    for m in QUANTITY_RE.finditer(text):
        start, end = m.start(), m.end()
        if overlaps(start, end):
            continue
        # Skip numbers glued to letters on the left ("IP55", "M25", "Fe500").
        prev = text[start - 1] if start > 0 else ""
        if prev and re.match(r"[A-Za-z]", prev) and not m.group("pm"):
            continue

        unit_def = lookup_unit(m.group("u") or "")
        if not unit_def:
            continue
        first_unit = lookup_unit(m.group("ua")) if m.group("ua") else None
        if first_unit and first_unit.dimension != unit_def.dimension:
            continue

        a = _tidy(to_canonical(_parse_num(m.group("a")), first_unit or unit_def))
        has_b = m.group("b") is not None
        b = _tidy(to_canonical(_parse_num(m.group("b")), unit_def)) if has_b else None
        if not math.isfinite(a) or (b is not None and not math.isfinite(b)):
            continue
        # "-" between two numbers is a range only when the second is larger;
        # otherwise it is punctuation (e.g. "40-5 °C" is not a range).
        if has_b and m.group("sep") == "-" and b is not None and b < a:
            continue

        comparator = "eq"
        qmin: Optional[float] = a
        qmax: Optional[float] = a
        tolerance: Optional[float] = None
        value: Optional[float] = a

        if m.group("pm"):
            # Stand-alone "±10 %" is a symmetric variation magnitude.
            comparator = "tolerance"
            tolerance = a / 100 if unit_def.unit == "%" else None
        elif b is not None:
            comparator = "range"
            qmin, qmax, value = min(a, b), max(a, b), None
        elif m.group("tol"):
            comparator = "tolerance"
            tol = float(m.group("tol"))
            tolu = m.group("tolu")
            tol_unit = lookup_unit(tolu) if tolu and tolu != "%" else None
            if tol_unit:
                delta = to_canonical(tol, tol_unit) - tol_unit.offset
                qmin, qmax = a - delta, a + delta
                tolerance = delta / abs(a) if a != 0 else None
            else:
                tolerance = tol / 100
                qmin = _tidy(a * (1 - tolerance))
                qmax = _tidy(a * (1 + tolerance))
        else:
            before = text[max(0, start - 30) : start]
            cmp = None if BETWEEN_PREFIX.search(before) else _comparator_for(text, start, end)
            if cmp == "min":
                comparator, qmax = "min", None
            elif cmp == "max":
                comparator, qmin = "max", None

        taken.append((start, end))
        out.append(
            Quantity(
                raw=m.group(0).strip(),
                span=TextSpan(base + start, base + end),
                value=value,
                min=qmin,
                max=qmax,
                unit=unit_def.unit,
                dimension=unit_def.dimension,
                comparator=comparator,
                tolerance=tolerance,
            )
        )

    return sorted(out, key=lambda q: q.span.start)


@dataclass
class InferredParameter:
    key: str
    signal: str


_SHORT_CIRCUIT_CUE = re.compile(r"\b(short[\s-]?circuit|fault|withstand|breaking capacity|icu|ics)\b")
_CUE_RES: dict[str, re.Pattern[str]] = {}


def _cue_re(cue: str) -> re.Pattern[str]:
    pattern = _CUE_RES.get(cue)
    if pattern is None:
        pattern = _CUE_RES[cue] = re.compile(r"\b" + re.escape(cue))
    return pattern


def infer_parameter(text: str, quantity: Quantity, base: int = 0) -> Optional[InferredParameter]:
    """Decide which specification parameter a quantity describes.

    Uses the nearest cue phrase before it (or shortly after it) in the same
    text. Returns None when the dimension alone is too ambiguous (e.g. bare
    lengths).
    """
    lower = text.lower()
    q_start = quantity.span.start - base
    q_end = quantity.span.end - base
    best: Optional[tuple[str, float, str]] = None

    for param in PARAMETERS:
        if quantity.dimension not in param.dimensions:
            continue
        for cue in param.cues:
            for m in _cue_re(cue).finditer(lower):
                cue_end = m.start() + len(cue)
                if cue_end <= q_start:
                    distance = q_start - cue_end
                elif m.start() >= q_end:
                    distance = (m.start() - q_end) * 2 + 10  # prefer cues before the value
                else:
                    continue
                if distance > 90:
                    continue
                # Longer, more specific cues win ties.
                weighted = distance - len(cue) * 0.5
                if best is None or weighted < best[1]:
                    best = (param.key, weighted, cue)

    # A kA-scale current next to a short-circuit cue is a withstand/breaking
    # rating, even when a closer generic cue ("busbar") names the component.
    magnitude = quantity.value if quantity.value is not None else (quantity.min if quantity.min is not None else 0)
    if quantity.dimension == "current" and magnitude >= 1000 and _SHORT_CIRCUIT_CUE.search(lower):
        return InferredParameter("short_circuit_rating", f"kA-scale current {quantity.raw} with a short-circuit cue")
    if best:
        return InferredParameter(best[0], f'cue "{best[2]}" near {quantity.raw}')
    fallback = DEFAULT_PARAMETER_FOR_DIMENSION.get(quantity.dimension)
    return InferredParameter(fallback, f"default parameter for {quantity.dimension}") if fallback else None


def interval_of(q: Quantity) -> tuple[float, float]:
    """Closed interval implied by a quantity; open ends become ±infinity."""
    return (q.min if q.min is not None else -math.inf, q.max if q.max is not None else math.inf)
