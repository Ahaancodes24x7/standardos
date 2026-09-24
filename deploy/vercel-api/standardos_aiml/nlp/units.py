"""Unit canonicalisation.

Every quantity is converted to one canonical unit per physical dimension so
values stated as "0.415 kV" and "415 V", or "25 N/mm²" and "25 MPa", compare
directly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from ..config import current
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
    if current().units_v3:
        return _lookup_v3(surface)
    direct = SURFACE_FORMS.get(surface) or (EXTRA_V2.get(surface) if current().units_v2 else None)
    if direct:
        return direct
    collapsed = re.sub(r"\s+", " ", surface)
    if collapsed in SURFACE_FORMS:
        return SURFACE_FORMS[collapsed]
    lower = collapsed.lower()
    if lower in CASE_INSENSITIVE:
        key = next((form for form in SORTED_FORMS if form.lower() == lower), None)
        return SURFACE_FORMS[key] if key else None
    if current().units_v2 and collapsed.isupper():
        # ALL-CAPS clauses ("1 OHMS", "40 DEG C", "300 SQ MM"): match forms case-insensitively,
        # preferring the lower-case spelling ("MM" → mm, not a mega-unit).
        key = next((form for form in sorted(SORTED_FORMS, key=lambda f: (f != f.lower(), -len(f))) if form.lower() == lower), None)
        return SURFACE_FORMS[key] if key else None
    return None


# v2 surface forms: flow in million/kilo litres per day (water supply tenders).
EXTRA_V2: dict[str, UnitDef] = {
    "MLD": _u("m3/h", "flow", 1000 / 24),
    "KLD": _u("m3/h", "flow", 1 / 24),
}


def unit_pattern_v2() -> str:
    """Unit alternation including ALL-CAPS variants of every form and the v2 extras."""
    forms = set(SURFACE_FORMS) | set(EXTRA_V2)
    forms |= {f.upper() for f in SURFACE_FORMS if f.upper() != f}
    return "|".join(re.escape(f) for f in sorted(forms, key=len, reverse=True))


# ---------------------------------------------------------------------------
# v3: spelling-robust units. Real tenders spell the same unit many ways
# ("Amperes", "AMPS", "k.W.", "Sq mm", "m^3/h", "cu.m/hr", "mg per litre",
# "degree centigrade", "℃"). Rather than listing every document's spelling,
# v3 adds spelled-out, dotted and "per" forms and matches every form in any
# letter case — except prefix-sensitive symbols, where case changes the value.
# ---------------------------------------------------------------------------

EXTRA_V3: dict[str, UnitDef] = {
    # temperature
    "℃": _u("degC", "temperature"),
    "deg.C": _u("degC", "temperature"),
    "degree centigrade": _u("degC", "temperature"),
    "degrees centigrade": _u("degC", "temperature"),
    "deg centigrade": _u("degC", "temperature"),
    "° Celsius": _u("degC", "temperature"),
    # voltage / current / power
    "kilovolt": _u("V", "voltage", 1000),
    "kilovolts": _u("V", "voltage", 1000),
    "k.V.": _u("V", "voltage", 1000),
    "kilo-volt": _u("V", "voltage", 1000),
    "amp.": _u("A", "current"),
    "kiloampere": _u("A", "current", 1000),
    "kiloamperes": _u("A", "current", 1000),
    "kilo-amperes": _u("A", "current", 1000),
    "k.A.": _u("A", "current", 1000),
    "watt": _u("W", "power"),
    "watts": _u("W", "power"),
    "kilowatt": _u("W", "power", 1000),
    "kilowatts": _u("W", "power", 1000),
    "k.W.": _u("W", "power", 1000),
    "kilo-watt": _u("W", "power", 1000),
    "kilovolt-ampere": _u("VA", "apparent_power", 1000),
    "kilo-volt-ampere": _u("VA", "apparent_power", 1000),
    "kilo-volt-amperes": _u("VA", "apparent_power", 1000),
    "k.V.A.": _u("VA", "apparent_power", 1000),
    # frequency / speed
    "hertz": _u("Hz", "frequency"),
    "cycles per second": _u("Hz", "frequency"),
    "cycles/second": _u("Hz", "frequency"),
    "c/s": _u("Hz", "frequency"),
    "cps": _u("Hz", "frequency"),
    "rev/min": _u("rpm", "rotational_speed"),
    "revolutions per minute": _u("rpm", "rotational_speed"),
    "r.p.m.": _u("rpm", "rotational_speed"),
    "rpm.": _u("rpm", "rotational_speed"),
    # resistance
    "ohm.": _u("ohm", "resistance"),
    "megohm": _u("ohm", "resistance", 1e6),
    "megohms": _u("ohm", "resistance", 1e6),
    # length
    "millimetre": _u("mm", "length"),
    "millimetres": _u("mm", "length"),
    "millimeter": _u("mm", "length"),
    "millimeters": _u("mm", "length"),
    "m.m.": _u("mm", "length"),
    "mm.": _u("mm", "length"),
    "centimetre": _u("mm", "length", 10),
    "centimetres": _u("mm", "length", 10),
    "mtr": _u("mm", "length", 1000),
    "mtrs": _u("mm", "length", 1000),
    "mtr.": _u("mm", "length", 1000),
    "kilometre": _u("mm", "length", 1e6),
    "kilometres": _u("mm", "length", 1e6),
    # area
    "sq. mm.": _u("mm2", "area"),
    "sq.mm.": _u("mm2", "area"),
    "square mm": _u("mm2", "area"),
    "square millimetre": _u("mm2", "area"),
    "square millimetres": _u("mm2", "area"),
    "mm sq": _u("mm2", "area"),
    "mm^2": _u("mm2", "area"),
    # flow
    "m^3/h": _u("m3/h", "flow"),
    "m^3/hr": _u("m3/h", "flow"),
    "m3/hour": _u("m3/h", "flow"),
    "m³/hour": _u("m3/h", "flow"),
    "m3 per hour": _u("m3/h", "flow"),
    "cu.m/hr": _u("m3/h", "flow"),
    "cu.m/h": _u("m3/h", "flow"),
    "cu m/hr": _u("m3/h", "flow"),
    "cu m/h": _u("m3/h", "flow"),
    "cum/h": _u("m3/h", "flow"),
    "cubic metre per hour": _u("m3/h", "flow"),
    "cubic metres per hour": _u("m3/h", "flow"),
    "cubic meters per hour": _u("m3/h", "flow"),
    "litres per second": _u("m3/h", "flow", 3.6),
    "litres per minute": _u("m3/h", "flow", 0.06),
    # concentration / density
    "mg per litre": _u("mg/L", "concentration"),
    "mg per liter": _u("mg/L", "concentration"),
    "milligram per litre": _u("mg/L", "concentration"),
    "milligrams per litre": _u("mg/L", "concentration"),
    "mg/liter": _u("mg/L", "concentration"),
    "mg/lit": _u("mg/L", "concentration"),
    "mg/ltr": _u("mg/L", "concentration"),
    "N.T.U.": _u("NTU", "turbidity"),
    "kg/m^3": _u("kg/m3", "density"),
    "kg/cu.m": _u("kg/m3", "density"),
    "kg/cu m": _u("kg/m3", "density"),
    "kg per cubic metre": _u("kg/m3", "density"),
    "kg per cubic meter": _u("kg/m3", "density"),
    "kg per cum": _u("kg/m3", "density"),
    "kg per m3": _u("kg/m3", "density"),
    # time
    "calendar days": _u("h", "time", 24),
    "working days": _u("h", "time", 24),
    # sound
    "dB (A)": _u("dB", "sound"),
    "decibels (A)": _u("dB", "sound"),
    "decibel (A)": _u("dB", "sound"),
    "decibels": _u("dB", "sound"),
    # ratio
    "pct": _u("%", "percent"),
    "per cent": _u("%", "percent"),
}

# Symbols whose letter case carries an SI prefix (milli vs mega) are matched exactly.
PREFIX_SENSITIVE = {"ma", "mv", "mw", "mω", "mpa", "mva", "mohm"}

ALL_V3: dict[str, UnitDef] = {**SURFACE_FORMS, **EXTRA_V2, **EXTRA_V3}
_BY_LOWER: dict[str, UnitDef] = {}
# Lower-case spellings first, so "MM" resolves to millimetres and "KVA" to kVA.
for _form in sorted(ALL_V3, key=lambda f: (f != f.lower(), -len(f))):
    _BY_LOWER.setdefault(_form.lower(), ALL_V3[_form])


def _lookup_v3(surface: str) -> Optional[UnitDef]:
    collapsed = re.sub(r"\s+", " ", surface.strip())
    for form in (collapsed, collapsed.rstrip(".")):
        if form in ALL_V3:
            return ALL_V3[form]
    lower = collapsed.lower()
    if lower in PREFIX_SENSITIVE:
        return None
    return _BY_LOWER.get(lower) or _BY_LOWER.get(lower.rstrip("."))


def unit_pattern_v3() -> str:
    """Alternation of every v3 form, longest first; matched case-insensitively (see quantities)."""
    forms = sorted(set(ALL_V3), key=len, reverse=True)
    return "|".join(re.escape(f).replace(r"\ ", r"\s*") for f in forms)


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
