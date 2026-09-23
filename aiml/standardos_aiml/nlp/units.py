"""Unit canonicalisation.

Every quantity is converted to one canonical unit per physical dimension so
values stated as "0.415 kV" and "415 V", or "25 N/mm²" and "25 MPa", compare
directly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from ..provenance import fmt_num


@dataclass(frozen=True)
class UnitDef:
    unit: str  # canonical unit symbol after conversion
    dimension: str
    factor: float = 1.0  # canonical = raw * factor + offset
    offset: float = 0.0


def _u(unit: str, dimension: str, factor: float = 1, offset: float = 0) -> UnitDef:
    return UnitDef(unit, dimension, factor, offset)


# Surface forms are matched case-sensitively unless listed in CASE_INSENSITIVE,
# because "mA" and "MA", or "m" and "M", differ.
SURFACE_FORMS: dict[str, UnitDef] = {
    # temperature
    "°C": _u("degC", "temperature"),
    "° C": _u("degC", "temperature"),
    "ºC": _u("degC", "temperature"),
    "deg C": _u("degC", "temperature"),
    "degC": _u("degC", "temperature"),
    "deg. C": _u("degC", "temperature"),
    "degree C": _u("degC", "temperature"),
    "degrees C": _u("degC", "temperature"),
    "degree Celsius": _u("degC", "temperature"),
    "degrees Celsius": _u("degC", "temperature"),
    "°F": _u("degC", "temperature", 5 / 9, -160 / 9),
    # voltage
    "V": _u("V", "voltage"),
    "volt": _u("V", "voltage"),
    "volts": _u("V", "voltage"),
    "kV": _u("V", "voltage", 1000),
    "KV": _u("V", "voltage", 1000),
    "mV": _u("V", "voltage", 0.001),
    # current
    "A": _u("A", "current"),
    "amp": _u("A", "current"),
    "amps": _u("A", "current"),
    "ampere": _u("A", "current"),
    "amperes": _u("A", "current"),
    "kA": _u("A", "current", 1000),
    "KA": _u("A", "current", 1000),
    "mA": _u("A", "current", 0.001),
    # power
    "W": _u("W", "power"),
    "kW": _u("W", "power", 1000),
    "KW": _u("W", "power", 1000),
    "MW": _u("W", "power", 1e6),
    "HP": _u("W", "power", 745.7),
    "hp": _u("W", "power", 745.7),
    "VA": _u("VA", "apparent_power"),
    "kVA": _u("VA", "apparent_power", 1000),
    "KVA": _u("VA", "apparent_power", 1000),
    "MVA": _u("VA", "apparent_power", 1e6),
    # frequency / speed
    "Hz": _u("Hz", "frequency"),
    "kHz": _u("Hz", "frequency", 1000),
    "rpm": _u("rpm", "rotational_speed"),
    "RPM": _u("rpm", "rotational_speed"),
    # resistance
    "Ω": _u("ohm", "resistance"),
    "ohm": _u("ohm", "resistance"),
    "ohms": _u("ohm", "resistance"),
    "MΩ": _u("ohm", "resistance", 1e6),
    "Mohm": _u("ohm", "resistance", 1e6),
    # length (canonical mm)
    "mm": _u("mm", "length"),
    "cm": _u("mm", "length", 10),
    "m": _u("mm", "length", 1000),
    "metre": _u("mm", "length", 1000),
    "metres": _u("mm", "length", 1000),
    "meter": _u("mm", "length", 1000),
    "meters": _u("mm", "length", 1000),
    "km": _u("mm", "length", 1e6),
    # area
    "mm²": _u("mm2", "area"),
    "mm2": _u("mm2", "area"),
    "sq mm": _u("mm2", "area"),
    "sq. mm": _u("mm2", "area"),
    "sq.mm": _u("mm2", "area"),
    "sqmm": _u("mm2", "area"),
    # pressure / stress (canonical MPa)
    "MPa": _u("MPa", "pressure"),
    "N/mm²": _u("MPa", "pressure"),
    "N/mm2": _u("MPa", "pressure"),
    "kPa": _u("MPa", "pressure", 0.001),
    "bar": _u("MPa", "pressure", 0.1),
    "kg/cm²": _u("MPa", "pressure", 0.0980665),
    "kg/cm2": _u("MPa", "pressure", 0.0980665),
    "kgf/cm²": _u("MPa", "pressure", 0.0980665),
    "kgf/cm2": _u("MPa", "pressure", 0.0980665),
    # flow (canonical m3/h)
    "m³/h": _u("m3/h", "flow"),
    "m3/h": _u("m3/h", "flow"),
    "m3/hr": _u("m3/h", "flow"),
    "m³/hr": _u("m3/h", "flow"),
    "cum/hr": _u("m3/h", "flow"),
    "lps": _u("m3/h", "flow", 3.6),
    "LPS": _u("m3/h", "flow", 3.6),
    "l/s": _u("m3/h", "flow", 3.6),
    "L/s": _u("m3/h", "flow", 3.6),
    "lpm": _u("m3/h", "flow", 0.06),
    "LPM": _u("m3/h", "flow", 0.06),
    "l/min": _u("m3/h", "flow", 0.06),
    "L/min": _u("m3/h", "flow", 0.06),
    # concentration
    "mg/l": _u("mg/L", "concentration"),
    "mg/L": _u("mg/L", "concentration"),
    "mg/litre": _u("mg/L", "concentration"),
    "ppm": _u("mg/L", "concentration"),
    "NTU": _u("NTU", "turbidity"),
    # mass & density
    "kg": _u("kg", "mass"),
    "kg/m³": _u("kg/m3", "density"),
    "kg/m3": _u("kg/m3", "density"),
    "kg/cum": _u("kg/m3", "density"),
    # time
    "h": _u("h", "time"),
    "hr": _u("h", "time"),
    "hrs": _u("h", "time"),
    "hour": _u("h", "time"),
    "hours": _u("h", "time"),
    "min": _u("h", "time", 1 / 60),
    "minutes": _u("h", "time", 1 / 60),
    "day": _u("h", "time", 24),
    "days": _u("h", "time", 24),
    "weeks": _u("h", "time", 168),
    "year": _u("h", "time", 8760),
    "years": _u("h", "time", 8760),
    "months": _u("h", "time", 730),
    # sound
    "dB": _u("dB", "sound"),
    "dB(A)": _u("dB", "sound"),
    "dBA": _u("dB", "sound"),
    # ratio
    "%": _u("%", "percent"),
    "percent": _u("%", "percent"),
}

CASE_INSENSITIVE = {
    "day",
    "days",
    "weeks",
    "volt",
    "volts",
    "amp",
    "amps",
    "ampere",
    "amperes",
    "ohm",
    "ohms",
    "metre",
    "metres",
    "meter",
    "meters",
    "hour",
    "hours",
    "minutes",
    "year",
    "years",
    "months",
    "percent",
    "degree celsius",
    "degrees celsius",
}

SORTED_FORMS = sorted(SURFACE_FORMS, key=len, reverse=True)

# Alternation matching any unit surface form; longest forms first.
UNIT_PATTERN = "|".join(re.escape(form) for form in SORTED_FORMS)


def lookup_unit(surface: str) -> Optional[UnitDef]:
    direct = SURFACE_FORMS.get(surface)
    if direct:
        return direct
    collapsed = re.sub(r"\s+", " ", surface)
    if collapsed in SURFACE_FORMS:
        return SURFACE_FORMS[collapsed]
    lower = collapsed.lower()
    if lower in CASE_INSENSITIVE:
        key = next((form for form in SORTED_FORMS if form.lower() == lower), None)
        return SURFACE_FORMS[key] if key else None
    return None


def to_canonical(value: float, unit: UnitDef) -> float:
    return value * unit.factor + unit.offset


def _n(x: float) -> str:
    if float(x).is_integer():
        return fmt_num(x)
    return fmt_num(float(f"{x:.3f}"))


def format_canonical(value: float, unit: str) -> str:
    """Render a canonical value back in a readable unit for findings and repairs."""
    if unit == "degC":
        return f"{_n(value)} °C"
    if unit == "V":
        return f"{_n(value / 1000)} kV" if value >= 1000 and value % 100 == 0 else f"{_n(value)} V"
    if unit == "W":
        return f"{_n(value / 1000)} kW" if value >= 1000 else f"{_n(value)} W"
    if unit == "VA":
        return f"{_n(value / 1000)} kVA" if value >= 1000 else f"{_n(value)} VA"
    if unit == "A":
        return f"{_n(value / 1000)} kA" if value >= 1000 else f"{_n(value)} A"
    if unit == "mm":
        return f"{_n(value / 1000)} m" if value >= 1000 and value % 1000 == 0 else f"{_n(value)} mm"
    if unit == "mm2":
        return f"{_n(value)} mm²"
    if unit == "MPa":
        return f"{_n(value)} MPa"
    if unit == "kg/m3":
        return f"{_n(value)} kg/m³"
    if unit in ("ratio", "pH"):
        return _n(value)
    return f"{_n(value)} {unit}"
