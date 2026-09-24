"""Standard designations, technical entities, text-valued parameters and product terms."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional

from ..config import current
from ..types import Entity, StandardReference, TextSpan

# ---------------------------------------------------------------------------
# Standard designations
# ---------------------------------------------------------------------------

# Matches IS, IS/IEC, IS/ISO and bare IEC/ISO designations with optional
# part/section and year, e.g. "IS:732-2019", "IS 1554 (Part 1):1988",
# "IS/IEC 61439-1:2020", "IS 516 (Part 1/Sec 1)", "IEC 60529".
REF_RE = re.compile(
    r"\b(?P<prefix>I\.?\s?S\.?\s*/\s*(?:IEC|ISO)|IS\s*/\s*(?:IEC|ISO)|I\.S\.|IS|IEC|ISO)\s*[:-]?\s*(?P<num>\d{2,5})"
    r"(?:\s*[-‐]\s*(?P<dashPart>\d{1,2})(?!\d))?"
    r"(?:\s*\(\s*(?:Part|Pt\.?)\s*(?P<part>[0-9A-Z]{1,3})(?:\s*/\s*Sec(?:tion)?\.?\s*(?P<sec>\d{1,2}))?\s*\))?"
    r"(?:\s*,?\s*(?:Part|Pt\.?)[\s-]*(?P<partWord>\d{1,2})(?!\d))?"
    r"(?:\s*[:-]\s*(?P<year>(?:19|20)\d{2})(?!\d))?"
)


def canonical_designation(prefix: str, num: str, part: Optional[str] = None, sec: Optional[str] = None) -> str:
    family = re.sub(r"\s+", "", prefix.replace(".", "")).upper()
    if family in ("IS/IEC", "IS/ISO", "IEC", "ISO"):
        base = f"{family} {num}"
        return f"{base}-{part}" if part else base
    out = f"IS {num}"
    if part:
        out += f" (Part {part}/Sec {sec})" if sec else f" (Part {part})"
    return out


def extract_standard_references(text: str, base: int = 0) -> list[StandardReference]:
    out: list[StandardReference] = []
    for m in REF_RE.finditer(text):
        part = m.group("part") or m.group("dashPart") or m.group("partWord")
        year = int(m.group("year")) if m.group("year") else None
        raw = m.group(0)
        out.append(
            StandardReference(
                raw=raw.strip(),
                span=TextSpan(base + m.start(), base + m.start() + len(raw.rstrip())),
                designation=canonical_designation(m.group("prefix") or "IS", m.group("num"), part, m.group("sec")),
                year=year,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Technical entities
# ---------------------------------------------------------------------------


def _normalise_material(raw: str) -> str:
    lower = raw.lower()
    if lower.startswith("alumin"):
        return "aluminium"
    if lower.startswith("galvani"):
        return "galvanised steel"
    if lower in ("pvc", "xlpe", "hdpe", "crca"):
        return lower.upper()
    return lower


@dataclass(frozen=True)
class _EntityRule:
    kind: str
    pattern: re.Pattern[str]
    value: Callable[[re.Match[str]], str]
    requires: Optional[re.Pattern[str]] = None


ENTITY_RULES: list[_EntityRule] = [
    _EntityRule(
        "ip_rating",
        re.compile(r"\bIP\s?-?\s?([0-6X])([0-9X])([A-DHMSW])?\b"),
        lambda m: f"IP{m.group(1)}{m.group(2)}{m.group(3) or ''}",
    ),
    _EntityRule(
        "concrete_grade",
        re.compile(r"\bM\s?-?\s?(10|15|20|25|30|35|40|45|50|55|60|65|70|75|80)\b"),
        lambda m: f"M{m.group(1)}",
        re.compile(r"\b(concrete|grade|rcc|pcc|mix|footing|slab|column|beam|foundation|structural)\b", re.I),
    ),
    _EntityRule(
        "steel_grade",
        re.compile(r"\bFe\s?-?\s?(250|415|500|550|600)\s?(D|S)?\b"),
        lambda m: f"Fe {m.group(1)}{m.group(2) or ''}",
    ),
    _EntityRule(
        "material",
        re.compile(
            r"\b(copper|alumin(?:i)?um|PVC|XLPE|HDPE|galvani[sz]ed|stainless steel|cast iron|bronze|CRCA)\b", re.I
        ),
        lambda m: _normalise_material(m.group(1)),
    ),
    _EntityRule(
        "certification",
        re.compile(
            r"\b(ISI[\s-]mark(?:ed|ing)?|Standard Mark(?:ed|ing)?|BIS licen[cs]e|BIS certifi(?:cation|ed)|type[\s-]test(?:ed)?\s+(?:report|certificate)s?"
            r"|test certificates?|test reports?|NABL|certificate of conformity|BEE star label(?:ling)?)\b",
            re.I,
        ),
        # "ISI marked" / "ISI marking" are the usual tender wording for the Standard Mark.
        lambda m: re.sub(r"^(isi|standard)[\s-]mark(?:ed|ing)?$", r"\1 mark", m.group(1).lower()),
    ),
    _EntityRule(
        "test",
        re.compile(
            r"\b(routine tests?|type tests?|acceptance tests?|factory acceptance tests?|witness(?:ed)? tests?|tested|testing|tests?\s+shall)\b",
            re.I,
        ),
        lambda m: re.sub(r"\s+shall$", "", m.group(1).lower()),
    ),
]


def extract_entities(text: str, base: int = 0) -> list[Entity]:
    out: list[Entity] = []
    for rule in ENTITY_RULES:
        if rule.requires and not rule.requires.search(text):
            continue
        for m in rule.pattern.finditer(text):
            out.append(
                Entity(kind=rule.kind, value=rule.value(m), raw=m.group(0), span=TextSpan(base + m.start(), base + m.end()))
            )
    return sorted(out, key=lambda e: e.span.start)


def _expand_cement(raw: str) -> str:
    upper = raw.upper()
    if upper == "OPC" or "ORDINARY" in upper:
        return "OPC"
    if upper == "PPC" or "POZZOLANA" in upper:
        return "PPC"
    if upper == "PSC" or "SLAG" in upper:
        return "PSC"
    return raw


@dataclass(frozen=True)
class _TextParamRule:
    parameter: str
    pattern: re.Pattern[str]
    value: Callable[[re.Match[str]], str]


# Text-valued parameters extracted directly from wording.
TEXT_PARAMS: list[_TextParamRule] = [
    _TextParamRule("efficiency_class", re.compile(r"\bIE\s?-?\s?([1-5])\b"), lambda m: f"IE{m.group(1)}"),
    _TextParamRule(
        "efficiency_class",
        re.compile(r"\benergy\s+efficiency\s+level\s*[-:]?\s*([1-3])\b", re.I),
        lambda m: f"Level {m.group(1)}",
    ),
    _TextParamRule(
        "efficiency_class",
        re.compile(r"\b([1-5])\s*star\s+(?:rated|rating|label\w*)\b", re.I),
        lambda m: f"{m.group(1)} star",
    ),
    _TextParamRule(
        "insulation_class",
        re.compile(
            r"\b(?:class\s*[-:]?\s*([BFH])\s+insulation|insulation\s+class\s*[-:]?\s*([BFH])|class\s+([BFH])\b(?=[^.]{0,40}insulat))",
            re.I,
        ),
        lambda m: f"Class {(m.group(1) or m.group(2) or m.group(3) or '').upper()}",
    ),
    _TextParamRule(
        "duty_type",
        re.compile(r"\b(?:duty\s*(?:type|cycle)?\s*[-:]?\s*S([1-9])|S([1-9])\s+(?:duty|continuous))\b", re.I),
        lambda m: f"S{m.group(1) or m.group(2)}",
    ),
    _TextParamRule(
        "exposure_condition",
        re.compile(
            r"\b(?:(very\s+severe|mild|moderate|severe|extreme)\s+(?:exposure|environment)"
            r"|exposure\s+(?:condition|class)?\s*(?:shall be|is|as|:|-|of)?\s*(?:considered\s+(?:as\s+)?)?[\"'“]?(very\s+severe|mild|moderate|severe|extreme))\b",
            re.I,
        ),
        lambda m: re.sub(r"\s+", " ", (m.group(1) or m.group(2) or "").lower()),
    ),
    _TextParamRule(
        "cement_type",
        re.compile(
            r"\b(OPC|PPC|PSC|ordinary portland cement|portland pozzolana cement|portland slag cement)"
            r"(?:\s*(?:of\s+)?(?:grade\s*)?(33|43|53)(?:\s*grade)?)?\b",
            re.I,
        ),
        lambda m: f"{_expand_cement(m.group(1))}{f' {m.group(2)} grade' if m.group(2) else ''}",
    ),
    _TextParamRule(
        "earthing_system",
        re.compile(r"\b(TN-S|TN-C-S|TN-C|TT)\b(?=\s*(?:system|earthing|arrangement))"),
        lambda m: m.group(1),
    ),
    _TextParamRule(
        "bacteriological_quality",
        re.compile(
            r"\b(E\.?\s?coli|(?:total|thermotolerant)\s+coliforms?)\b[^.]{0,60}?\b(not\s+(?:be\s+)?detectable|absent|nil|shall not be detected)",
            re.I,
        ),
        lambda m: f"{re.sub(r'\s+', ' ', m.group(1))} not detectable",
    ),
]


@dataclass
class TextParameter:
    parameter: str
    value: str
    raw: str


def extract_text_parameters(text: str) -> list[TextParameter]:
    out: list[TextParameter] = []
    for rule in TEXT_PARAMS:
        for m in rule.pattern.finditer(text):
            out.append(TextParameter(rule.parameter, rule.value(m), m.group(0)))
    return out


# ---------------------------------------------------------------------------
# Product / domain terms (retrieval features)
# ---------------------------------------------------------------------------

# Canonical product term → surface forms (lower case). Order: specific first.
PRODUCT_TERMS: list[tuple[str, list[str]]] = [
    ("submersible pump", ["submersible pump", "submersible pumpset", "borewell pump", "submersible pumps"]),
    ("centrifugal pump", ["centrifugal pump", "end suction pump", "monoblock pump", "horizontal pump"]),
    ("pump", ["pump", "pumps", "pumpset", "pumping set"]),
    (
        "induction motor",
        ["induction motor", "squirrel cage", "three phase motor", "3 phase motor", "3-phase motor", "motors", "motor"],
    ),
    ("transformer", ["distribution transformer", "transformer", "transformers"]),
    (
        "switchgear assembly",
        [
            "switchgear",
            "switchboard",
            "distribution panel",
            "distribution board",
            "control panel",
            "lt panel",
            "mcc panel",
            "pcc panel",
            "panel",
            "panels",
            "assembly",
            "assemblies",
        ],
    ),
    ("circuit breaker", ["circuit breaker", "circuit-breaker", "mccb", "acb", "breakers"]),
    ("miniature circuit breaker", ["mcb", "mcbs", "miniature circuit breaker"]),
    ("residual current device", ["rccb", "rcd", "elcb", "residual current", "earth leakage"]),
    ("cable", ["cable", "cables", "wire", "wires", "wiring"]),
    (
        "earthing",
        [
            "earthing",
            "grounding",
            "earth electrode",
            "earth pit",
            "protective earth",
            "earth continuity",
            "protective conductor",
        ],
    ),
    ("concrete", ["concrete", "rcc", "pcc", "reinforced cement concrete", "ready mixed concrete", "rmc"]),
    ("reinforcement steel", ["reinforcement", "tmt", "rebar", "rebars", "steel bars", "hysd"]),
    ("structural steel", ["structural steel", "rolled steel", "steel sections", "plates"]),
    ("aggregate", ["aggregate", "aggregates", "sand", "coarse aggregate", "fine aggregate"]),
    ("cement", ["cement", "opc", "ppc"]),
    ("drinking water", ["drinking water", "potable water", "treated water", "water supply", "water quality"]),
    ("packaged drinking water", ["packaged drinking water", "bottled water", "packaged water"]),
]

# v2: surface forms missing in 2.1 (audit: "flexible cords" found no product).
_V2_EXTRA = {
    "cable": ["cord", "cords", "flexible cord"],
    "switchgear assembly": ["busbar", "busbars", "switch board"],
    "earthing": ["earth electrodes", "earth resistance", "earth pits"],
    "residual current device": ["rccbs", "rcds", "elcbs"],
}
PRODUCT_TERMS_V2: list[tuple[str, list[str]]] = [(c, [*forms, *_V2_EXTRA.get(c, [])]) for c, forms in PRODUCT_TERMS]


def _compile(table: list[tuple[str, list[str]]]) -> list[tuple[str, list[re.Pattern[str]]]]:
    return [
        (canonical, [re.compile("[^a-z]" + re.sub(r"[-/]", "[-/ ]?", form) + "[^a-z]") for form in forms])
        for canonical, forms in table
    ]


_PRODUCT_RES = _compile(PRODUCT_TERMS)
_PRODUCT_RES_V2 = _compile(PRODUCT_TERMS_V2)


def extract_product_terms(text: str) -> list[str]:
    lower = f" {text.lower()} "
    table = _PRODUCT_RES_V2 if current().product_terms_v2 else _PRODUCT_RES
    return [canonical for canonical, patterns in table if any(p.search(lower) for p in patterns)]
