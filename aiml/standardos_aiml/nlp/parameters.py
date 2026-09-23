"""Controlled vocabulary of specification parameters.

Requirement attributes, clause constraints and standard checklists all use
these keys, which is what lets the reasoning layer compare a tender value with
a standard's limit.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParameterDef:
    key: str
    label: str
    dimensions: tuple[str, ...]  # dimensions a quantity may have; empty = text-valued
    cues: tuple[str, ...]  # lower-case phrases that indicate the parameter near a value
    mention_cues: tuple[str, ...] = field(default=())  # phrases that mention it without a value


def _p(key: str, label: str, dimensions: list[str], cues: list[str], mention: list[str] | None = None) -> ParameterDef:
    return ParameterDef(key, label, tuple(dimensions), tuple(cues), tuple(mention or ()))


PARAMETERS: list[ParameterDef] = [
    _p(
        "ambient_temperature",
        "Ambient temperature",
        ["temperature"],
        [
            "ambient",
            "surrounding air",
            "operating temperature",
            "service temperature",
            "room temperature",
            "site temperature",
            "design temperature",
        ],
    ),
    _p(
        "conductor_temperature",
        "Conductor operating temperature",
        ["temperature"],
        ["conductor temperature", "conductor operating temperature", "continuous conductor"],
    ),
    _p("relative_humidity", "Relative humidity", ["percent"], ["humidity", "rh"]),
    _p("altitude", "Installation altitude", ["length"], ["altitude", "above mean sea level", "amsl", "elevation"]),
    _p(
        "rated_voltage",
        "Rated voltage",
        ["voltage"],
        ["voltage", "volt", "supply", "rated", "working", "system", "grade"],
        ["voltage"],
    ),
    _p(
        "voltage_variation",
        "Permissible voltage variation",
        ["percent"],
        [
            "voltage variation",
            "voltage fluctuation",
            "voltage tolerance",
            "variation in voltage",
            "variation in supply voltage",
            "voltage",
        ],
    ),
    _p("frequency", "Supply frequency", ["frequency"], ["frequency", "supply"], ["frequency"]),
    _p(
        "frequency_variation",
        "Permissible frequency variation",
        ["percent"],
        ["frequency variation", "variation in frequency", "frequency"],
    ),
    _p(
        "rated_power",
        "Rated output power",
        ["power"],
        ["output", "rated", "power", "rating", "capacity", "motor"],
        ["rated output", "power rating"],
    ),
    _p(
        "apparent_power",
        "Rated apparent power",
        ["apparent_power"],
        ["rating", "capacity", "transformer", "rated"],
        ["kva rating"],
    ),
    _p(
        "rated_current",
        "Rated current",
        ["current"],
        ["rated current", "current rating", "busbar", "incomer", "outgoing", "current"],
    ),
    _p(
        "short_circuit_rating",
        "Short-circuit withstand rating",
        ["current"],
        ["short circuit", "short-circuit", "fault level", "fault current", "withstand", "breaking capacity"],
        ["short circuit", "short-circuit", "fault level"],
    ),
    _p("efficiency", "Efficiency at rated duty", ["percent"], ["efficiency"], ["efficiency", "efficient", "energy saving"]),
    _p(
        "efficiency_class",
        "Efficiency class",
        [],
        [],
        ["efficiency class", "ie class", "energy efficient", "energy-efficient", "high efficiency"],
    ),
    _p(
        "ip_rating",
        "Degree of protection (IP code)",
        [],
        [],
        [
            "ingress",
            "degree of protection",
            "dust",
            "splash",
            "weatherproof",
            "vermin proof",
            "enclosure protection",
        ],
    ),
    _p("insulation_class", "Insulation class", [], [], ["insulation class", "class of insulation"]),
    _p("duty_type", "Duty type", [], [], ["duty type", "continuous duty", "duty cycle"]),
    _p(
        "flow_rate",
        "Rated flow (discharge)",
        ["flow"],
        ["discharge", "flow", "capacity", "delivery"],
        ["discharge", "flow rate"],
    ),
    _p(
        "pump_head",
        "Total head at duty point",
        ["length"],
        ["head", "tdh", "total dynamic head", "total head"],
        ["total head", "delivery head", "pumping head", "head at"],
    ),
    _p("speed", "Rated speed", ["rotational_speed"], ["speed", "rpm"]),
    _p(
        "conductor_size",
        "Conductor cross-section",
        ["area"],
        ["cross-section", "cross section", "size", "core", "conductor", "cable"],
        ["conductor size", "cross-sectional area"],
    ),
    _p("conductor_material", "Conductor material", [], [], ["conductor"]),
    _p("insulation_material", "Insulation material", [], [], ["insulation", "insulated"]),
    _p("earthing_system", "Earthing arrangement", [], [], ["earthing", "grounding", "earth electrode", "earth pit"]),
    _p(
        "earth_resistance",
        "Earth electrode resistance",
        ["resistance"],
        ["earth resistance", "earthing resistance", "electrode resistance", "resistance to earth", "earth"],
    ),
    _p("concrete_grade", "Concrete grade", ["pressure"], [], ["grade of concrete", "concrete grade", "concrete"]),
    _p("exposure_condition", "Exposure condition", [], [], ["exposure"]),
    _p("nominal_cover", "Nominal cover to reinforcement", ["length"], ["cover"], ["cover"]),
    _p(
        "water_cement_ratio",
        "Maximum free water–cement ratio",
        ["ratio"],
        ["water-cement", "water cement", "w/c"],
        ["water-cement ratio", "water cement ratio", "w/c ratio"],
    ),
    _p("cement_content", "Minimum cement content", ["density"], ["cement content", "cement"], ["cement content"]),
    _p("cement_type", "Cement type and grade", [], [], ["cement"]),
    _p("steel_grade", "Reinforcement steel grade", [], [], ["reinforcement", "tmt", "rebar", "steel bars"]),
    _p("elongation", "Minimum elongation", ["percent"], ["elongation"]),
    _p(
        "compressive_strength",
        "Compressive strength",
        ["pressure"],
        ["compressive strength", "characteristic strength", "cube strength", "strength"],
    ),
    _p("aggregate_size", "Nominal maximum aggregate size", ["length"], ["aggregate"]),
    _p("ph", "pH", ["ph"], ["ph"], ["ph"]),
    _p(
        "tds",
        "Total dissolved solids",
        ["concentration"],
        ["total dissolved solids", "tds", "dissolved solids"],
        ["total dissolved solids", "tds"],
    ),
    _p("turbidity", "Turbidity", ["turbidity"], ["turbidity"], ["turbidity"]),
    _p("fluoride", "Fluoride", ["concentration"], ["fluoride"], ["fluoride"]),
    _p("nitrate", "Nitrate", ["concentration"], ["nitrate"], ["nitrate"]),
    _p("chloride", "Chloride", ["concentration"], ["chloride"], ["chloride"]),
    _p("arsenic", "Arsenic", ["concentration"], ["arsenic"], ["arsenic"]),
    _p("total_hardness", "Total hardness", ["concentration"], ["hardness"], ["hardness"]),
    _p(
        "bacteriological_quality",
        "Bacteriological quality",
        [],
        [],
        ["e. coli", "e.coli", "coliform", "bacteriological", "microbiological"],
    ),
    _p("noise_level", "Noise level", ["sound"], ["noise", "sound pressure", "sound level"]),
    _p(
        "test_method",
        "Test and verification method",
        [],
        [],
        ["test", "tested", "testing", "inspection", "verification", "verified"],
    ),
    _p(
        "conformity_evidence",
        "Conformity evidence",
        [],
        [],
        [
            "isi mark",
            "standard mark",
            "bis licence",
            "bis license",
            "bis certification",
            "type test",
            "test certificate",
            "test report",
            "certificate of conformity",
            "conformity",
        ],
    ),
]

PARAMETER_BY_KEY: dict[str, ParameterDef] = {p.key: p for p in PARAMETERS}

# Default parameter when a quantity's dimension appears with no stronger cue.
DEFAULT_PARAMETER_FOR_DIMENSION: dict[str, str] = {
    "temperature": "ambient_temperature",
    "voltage": "rated_voltage",
    "current": "rated_current",
    "power": "rated_power",
    "apparent_power": "apparent_power",
    "frequency": "frequency",
    "rotational_speed": "speed",
    "area": "conductor_size",
    "flow": "flow_rate",
    "turbidity": "turbidity",
    "resistance": "earth_resistance",
    "sound": "noise_level",
    "density": "cement_content",
    "ratio": "water_cement_ratio",
    "ph": "ph",
}


def parameter_label(key: str) -> str:
    param = PARAMETER_BY_KEY.get(key)
    return param.label if param else key.replace("_", " ")
