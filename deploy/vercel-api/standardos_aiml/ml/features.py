"""Feature extraction shared by the learned requirement classifiers.

Two views of a requirement:

* **text** — the sentence itself (for TF-IDF and the sentence encoder);
* **structure** — what the deterministic NLP layer already knows: the lexicon's
  per-category cue scores, the physical dimensions of its quantities, the kinds
  of entities it mentions, and the specification parameters it states. These
  are the "symbolic" half of the hybrid model.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import current, use_config, preset
from ..nlp.classify import classify_requirement
from ..nlp.entities import extract_entities, extract_standard_references
from ..nlp.parameters import PARAMETERS
from ..nlp.quantities import extract_quantities
from ..nlp.requirements import build_attributes
from ..types import REQUIREMENT_CATEGORIES, Attribute, Entity, Quantity

CATEGORIES = REQUIREMENT_CATEGORIES
DIMENSIONS = [
    "temperature", "voltage", "current", "power", "apparent_power", "frequency", "rotational_speed", "resistance",
    "length", "area", "pressure", "flow", "concentration", "turbidity", "density", "time", "sound", "percent", "ph", "ratio",
]
ENTITY_KINDS = ["ip_rating", "concrete_grade", "steel_grade", "material", "certification", "test"]
PARAMETER_KEYS = [p.key for p in PARAMETERS]
STRUCT_DIM = len(CATEGORIES) + len(DIMENSIONS) + len(ENTITY_KINDS) + len(PARAMETER_KEYS) + 2


@dataclass
class Structured:
    text: str
    quantities: list[Quantity]
    entities: list[Entity]
    attributes: list[Attribute]
    has_reference: bool


def structure(text: str) -> Structured:
    """Run the deterministic NLP layer on one sentence (v3 lexicon and units)."""
    cfg = current() if current().lexicon_version >= 2 else preset("v3")
    with use_config(cfg):
        quantities = extract_quantities(text)
        entities = extract_entities(text)
        refs = extract_standard_references(text)
        attributes = build_attributes(text, 0, quantities, entities, refs, [])
    return Structured(text, quantities, entities, attributes, bool(refs))


def lexicon_scores(s: Structured) -> tuple[list[float], str, float]:
    with use_config(preset("v3")):
        cls = classify_requirement(s.text, s.quantities, s.entities, s.attributes)
    total = sum(cls.scores.values()) or 1.0
    return [cls.scores.get(c, 0.0) / total for c in CATEGORIES], cls.category, cls.confidence


def struct_vector(s: Structured) -> list[float]:
    lex, _, conf = lexicon_scores(s)
    dims = {q.dimension for q in s.quantities}
    kinds = {e.kind for e in s.entities}
    params = {a.parameter for a in s.attributes if a.quantity is not None or a.text}
    return [
        *lex,
        *[1.0 if d in dims else 0.0 for d in DIMENSIONS],
        *[1.0 if k in kinds else 0.0 for k in ENTITY_KINDS],
        *[1.0 if p in params else 0.0 for p in PARAMETER_KEYS],
        1.0 if s.has_reference else 0.0,
        conf,
    ]
