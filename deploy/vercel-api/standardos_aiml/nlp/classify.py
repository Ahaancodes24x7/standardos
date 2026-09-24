"""Requirement category classification with a weighted cue lexicon.

A transparent lexicon is the baseline because (a) reviewers must be able to
see why a category was chosen and (b) it needs no training data. Learned
classifiers (``standardos_aiml.ml``) are compared against it by the evaluation
framework and can be selected with ``PipelineConfig.classifier``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..config import current
from ..types import Attribute, Entity, Quantity

CUES: dict[str, list[tuple[re.Pattern[str], float]]] = {
    "performance": [
        (
            re.compile(
                r"\b(efficiency|efficient|output|discharge|flow|head|duty point|duty|speed|performance|capacity|load|strength|throughput|rated duty)(?:s|es)?\b",
                re.I,
            ),
            1,
        )
    ],
    "electrical": [
        (
            re.compile(
                r"\b(voltage|volt|current|frequency|phase|busbar|breaker|mcb|mccb|acb|rccb|cable|conductor|wiring|circuit|short[\s-]circuit|fault level|relay|kva|transformer|switchgear|feeder|incomer|insulation class|class [bfh] insulation)(?:s|es)?\b",
                re.I,
            ),
            1,
        )
    ],
    "environmental": [
        (
            re.compile(
                r"\b(ambient|temperature|humidity|altitude|outdoor|indoor|dust|ingress|weather|corrosi\w*|exposure|rain|climat\w*|coastal|environment\w*|site conditions?)(?:s|es)?\b",
                re.I,
            ),
            1,
        )
    ],
    "safety": [
        (
            re.compile(
                r"\b(safety|safe|earthing|earthed|earth continuity|protective earth|shock|fire|hazard\w*|interlock\w*|guard\w*|emergency|leakage|flameproof|touch|arc flash|insulation resistance)(?:s|es)?\b",
                re.I,
            ),
            1.2,
        )
    ],
    "material": [
        (
            re.compile(
                r"\b(material|copper|alumin\w*|steel|cement|aggregate|pvc|xlpe|hdpe|galvani\w*|stainless|cast iron|bronze|crca|reinforcement|tmt|rebar|composition|grade of concrete)(?:s|es)?\b",
                re.I,
            ),
            1,
        )
    ],
    "dimensional": [
        (
            re.compile(
                r"\b(dimension\w*|size|thickness|diameter|length|width|height|depth|cover|cross[\s-]section\w*|weight|clearance|spacing)(?:s|es)?\b",
                re.I,
            ),
            1,
        )
    ],
    "testing": [
        (
            re.compile(
                r"\b(test|tests|tested|testing|inspection|inspected|routine|type test|acceptance test|witness\w*|sampl\w*|trial|verif\w*|measure\w*)(?:s|es)?\b",
                re.I,
            ),
            1.3,
        )
    ],
    "certification": [
        (
            re.compile(
                r"\b(isi|bis|licen[cs]e|certificat\w*|certified|standard mark|conformity|nabl|bee|star label\w*)(?:s|es)?\b",
                re.I,
            ),
            1.6,
        )
    ],
    "documentation": [
        (
            re.compile(
                r"\b(drawings?|manuals?|documentation|documents?|submit\w*|datasheets?|data sheets?|catalogues?|as[\s-]built|records?|handover|o&m|schedule of)(?:s|es)?\b",
                re.I,
            ),
            1,
        )
    ],
    "installation": [
        (
            re.compile(
                r"\b(install\w*|erect\w*|commission\w*|mount\w*|laying|laid|foundation|fixing|fixed|site|routing|terminat\w*)(?:s|es)?\b",
                re.I,
            ),
            1,
        )
    ],
    "quality": [
        (
            re.compile(
                r"\b(ph|turbidity|dissolved solids|tds|fluoride|nitrate|chloride|arsenic|hardness|coliform|e\.?\s?coli|potable|drinking water|water quality|bacteriological)(?:s|es)?\b",
                re.I,
            ),
            1.5,
        )
    ],
}

DIMENSION_BOOST: dict[str, tuple[str, float]] = {
    "voltage": ("electrical", 1.5),
    "current": ("electrical", 1.5),
    "frequency": ("electrical", 1.2),
    "apparent_power": ("electrical", 1.2),
    "power": ("performance", 1),
    "flow": ("performance", 1.5),
    "rotational_speed": ("performance", 1),
    "temperature": ("environmental", 1.2),
    "concentration": ("quality", 1.5),
    "turbidity": ("quality", 1.5),
    "ph": ("quality", 1.5),
    "area": ("dimensional", 0.8),
    "length": ("dimensional", 0.8),
    "pressure": ("performance", 0.8),
    "resistance": ("safety", 1),
}

ENTITY_BOOST: dict[str, tuple[str, float]] = {
    "ip_rating": ("environmental", 1.2),
    "concrete_grade": ("material", 1.5),
    "steel_grade": ("material", 1.5),
    "material": ("material", 0.8),
    "certification": ("certification", 2),
    "test": ("testing", 1),
}

PARAMETER_BOOST: dict[str, tuple[str, float]] = {
    "efficiency": ("performance", 1.5),
    "efficiency_class": ("performance", 1.5),
    "relative_humidity": ("environmental", 1),
    "altitude": ("environmental", 1),
    "nominal_cover": ("dimensional", 1.2),
    "water_cement_ratio": ("material", 1.2),
    "cement_content": ("material", 1.2),
    "exposure_condition": ("environmental", 1),
    "earth_resistance": ("safety", 1.5),
    "voltage_variation": ("electrical", 1),
}

# v2 additions: execution verbs for installation, earthing hardware for safety,
# marking for documentation, coatings for material, efficacy/workability for
# performance. Weights > 1 so a specific cue outweighs one incidental product noun.
CUES_V2: dict[str, list[tuple[re.Pattern[str], float]]] = {
    "installation": [
        (
            re.compile(
                r"\b(concealed|conduits?|recessed|drawn\s+through|laid|laying|trenche?s?|cable\s+trays?|glands?|lugs?|"
                r"terminat\w*|curing|cured|moist|formwork|shuttering|compact\w*|vibrat\w*|fabricat\w*|weld\w*|erect\w*|"
                r"mounted|mounting|plinth|foundation\s+bolts?)\b",
                re.I,
            ),
            1.6,
        )
    ],
    "safety": [
        (re.compile(r"\b(earth\s+electrodes?|earth\s+pits?|earth\s+resistance|earthing|earthed|rccbs?|residual\s+current|protective\s+conductor)\b", re.I), 1.6)
    ],
    "documentation": [
        (re.compile(r"\b(marked\s+with|marking|carry\s+marking|nameplate|rating\s+plate|manuals?|as-built|drawings?|catalogues?)\b", re.I), 1.5)
    ],
    "material": [(re.compile(r"\b(primer|paint(?:ed|ing)?|coats?|epoxy|galvani\w*|cast\s+iron|bronze|stainless)\b", re.I), 1.2)],
    "performance": [(re.compile(r"\b(efficacy|lm/w|slump|workability|discharge|duty\s+point|head)\b", re.I), 1.2)],
    "certification": [(re.compile(r"\b(certificates?|certified|isi\s+mark\w*|standard\s+mark|bis\s+licen[cs]e|type\s+test\s+(?:reports?|certificates?))\b", re.I), 1.6)],
}

PARAMETER_BOOST_V2: dict[str, tuple[str, float]] = {
    **PARAMETER_BOOST,
    "conductor_size": ("dimensional", 1.8),
    "nominal_cover": ("dimensional", 1.8),
    "aggregate_size": ("dimensional", 1.2),
    "conductor_temperature": ("electrical", 1.5),
    "rated_voltage": ("electrical", 2.0),
    "rated_current": ("electrical", 2.0),
    "short_circuit_rating": ("electrical", 2.0),
    "frequency": ("electrical", 1.2),
    "noise_level": ("environmental", 1.5),
    "ambient_temperature": ("environmental", 1.5),
    "rated_power": ("performance", 1.2),
    "flow_rate": ("performance", 1.5),
    "pump_head": ("performance", 1.2),
    "speed": ("performance", 1.0),
    "earth_resistance": ("safety", 1.5),
    "concrete_grade": ("material", 1.5),
    "cement_type": ("material", 1.2),
    "steel_grade": ("material", 1.2),
    "ph": ("quality", 1.5),
    "tds": ("quality", 1.5),
    "turbidity": ("quality", 1.5),
}

CATEGORY_LABELS: dict[str, str] = {
    "performance": "Performance",
    "electrical": "Electrical characteristics",
    "environmental": "Operating environment",
    "safety": "Safety & protection",
    "material": "Materials",
    "dimensional": "Dimensions",
    "testing": "Testing & inspection",
    "certification": "Certification",
    "documentation": "Documentation",
    "installation": "Installation",
    "quality": "Quality limits",
    "general": "General",
}


@dataclass
class Classification:
    category: str
    scores: dict[str, float]
    confidence: float
    signals: list[str]
    method: str = "lexicon"


def _weight(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def classify_requirement(
    text: str, quantities: list[Quantity], entities: list[Entity], attributes: list[Attribute]
) -> Classification:
    scores: dict[str, float] = {}
    signals: list[str] = []

    def add(category: str, weight: float, why: str) -> None:
        scores[category] = scores.get(category, 0) + weight
        signals.append(f"{category}+{_weight(weight)} ({why})")

    v2 = current().lexicon_version >= 2
    cue_sets = [CUES, CUES_V2] if v2 else [CUES]
    for category, cues in (item for table in cue_sets for item in table.items()):
        for pattern, weight in cues:
            hits = [m.group(0).lower() for m in pattern.finditer(text)]
            if hits:
                unique = list(dict.fromkeys(hits))[:3]
                add(category, weight * min(2, len(hits)), '"' + '", "'.join(unique) + '"')
    # v2: a quantity whose parameter is known is boosted by that parameter, not by its dimension
    # (a 90 °C *conductor* temperature is electrical; "1 m distance" in a noise limit is not dimensional).
    by_parameter = {id(a.quantity): a.parameter for a in attributes if a.quantity is not None}
    for q in quantities:
        param = by_parameter.get(id(q)) if v2 else None
        if param and param in PARAMETER_BOOST_V2:
            continue
        if v2 and any(a.parameter in PARAMETER_BOOST_V2 and a.quantity is not None for a in attributes) and q.dimension == "length":
            continue
        boost = DIMENSION_BOOST.get(q.dimension)
        if boost:
            add(boost[0], boost[1], f"{q.dimension} value {q.raw}")
    for e in entities:
        boost = ENTITY_BOOST.get(e.kind)
        if boost:
            add(boost[0], boost[1], f"{e.kind} {e.value}")
    for a in attributes:
        boost = (PARAMETER_BOOST_V2 if v2 and (a.quantity is not None or a.text) else PARAMETER_BOOST).get(a.parameter)
        if boost:
            add(boost[0], boost[1], f"parameter {a.parameter}")

    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    if not ranked or ranked[0][1] <= 0:
        return Classification("general", scores, 0.4, ["no category cues"])
    top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0
    # Margin-based confidence: 0.5 when tied, approaching 1 as the lead grows.
    confidence = 0.5 + 0.5 * ((top[1] - second) / top[1])
    return Classification(top[0], scores, confidence, signals)
