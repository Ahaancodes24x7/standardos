"""camelCase JSON rendering of engine dataclasses (the frontend/database wire format)."""

from __future__ import annotations

import dataclasses
from typing import Any


def camel(name: str) -> str:
    head, *rest = name.rstrip("_").split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest)


def to_wire(value: Any) -> Any:
    """Recursively convert dataclasses to plain JSON-compatible values.

    Dataclass field names become camelCase; dict keys are left untouched (they
    are data such as parameter names). Fields listed in a class's ``OMIT_NONE``
    are dropped when ``None``, mirroring optional properties in the TS contract.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        cls = type(value)
        omit_none = getattr(cls, "OMIT_NONE", frozenset())
        omit = getattr(cls, "OMIT", frozenset())
        names = getattr(cls, "WIRE_NAMES", {})
        out: dict[str, Any] = {}
        for f in dataclasses.fields(value):
            if f.name in omit:
                continue
            v = getattr(value, f.name)
            if v is None and f.name in omit_none:
                continue
            out[names.get(f.name, camel(f.name))] = to_wire(v)
        return out
    if isinstance(value, dict):
        return {k: to_wire(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_wire(v) for v in value]
    return value
