from __future__ import annotations

import math
from typing import Optional

from .types import Provenance
from .version import COMPONENT_VERSIONS


def clamp01(value: float) -> float:
    if value is None or not math.isfinite(value):
        return 0.0
    return min(1.0, max(0.0, value))


def js_round(value: float, digits: int = 3) -> float:
    """``Math.round(value * 10**digits) / 10**digits`` — halves round up, as in JavaScript."""
    factor = 10**digits
    return math.floor(value * factor + 0.5) / factor


def provenance(
    component: str,
    method: str,
    confidence: float,
    signals: list[str],
    model: Optional[str] = None,
) -> Provenance:
    return Provenance(
        component=component,
        component_version=COMPONENT_VERSIONS[component],
        method=method,
        confidence=js_round(clamp01(confidence)),
        signals=signals,
        model=model,
    )


def fmt_num(value: float) -> str:
    """Render a number the way JavaScript's ``String(number)`` does (``10`` not ``10.0``)."""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if math.isfinite(value) and value == int(value):
        return str(int(value))
    return repr(float(value))
