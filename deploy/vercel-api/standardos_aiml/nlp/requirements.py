"""Requirement segmentation, identification and attribute assembly."""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from typing import Callable, Optional

from ..config import current
from ..ingest.sections import locate
from ..provenance import provenance
from ..types import Attribute, Entity, Quantity, Section, StandardReference, StructuredRequirement, TextSpan
from .classify import classify_requirement
from .entities import extract_entities, extract_product_terms, extract_standard_references, extract_text_parameters
from .parameters import PARAMETERS
from .quantities import extract_quantities, infer_parameter

# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------

ENUMERATOR = re.compile(r"^(?:\d{1,2}(?:\.\d{1,3}){0,4}[.)]?|\(?[a-z]\)|\(?[ivx]{1,4}\)|•|-|\*|–)\s+", re.I)
ABBREVIATIONS = re.compile(
    r"(?:\b(?:No|Nos|approx|min|max|Cl|cl|i\.e|e\.g|etc|viz|Fig|Sr|Dt|Rs|sq|Pt|Sec|deg|hr|Ltd|Co|St|Amd|Dept|Govt|incl|Max|Min|Approx|Ref|vol|Vol|kg|Hz|E|Nr)|\b[A-Z])\.$"
)
# v2: "… 90 deg C. Next clause" — the capital before the period is a unit, not an initial.
ENDS_WITH_UNIT = re.compile(r"\d\s*(?:[°º]\s*)?(?:deg\.?\s*)?[A-Za-z/²³]*[A-Z]\.$")
BOUNDARY = re.compile(r"[.!?](?=\s+[\"'(]?[A-Z0-9•])")


@dataclass
class Segment:
    text: str
    start: int
    line_start: int


def _push_segment(segments: list[Segment], raw: str, start: int, line_start: int) -> None:
    lead = len(raw) - len(raw.lstrip())
    text = raw.strip()
    if text:
        segments.append(Segment(text, start + lead, line_start))


def segment(text: str) -> list[Segment]:
    """Split text into candidate units: one per line/list item, then per sentence."""
    segments: list[Segment] = []
    offset = 0
    for line in text.split("\n"):
        line_start = offset
        offset += len(line) + 1
        trimmed_start = len(line) - len(line.lstrip())
        body = line[trimmed_start:]
        body_start = line_start + trimmed_start
        enumerator = ENUMERATOR.match(body)
        if enumerator:
            body = body[enumerator.end() :]
            body_start += enumerator.end()
        if not body.strip():
            continue
        # Sentence split on terminal punctuation followed by a capital/opening.
        cursor = 0
        for m in BOUNDARY.finditer(body):
            candidate = body[cursor : m.start() + 1]
            if (ABBREVIATIONS.search(candidate) and not (current().segmentation_v2 and ENDS_WITH_UNIT.search(candidate))) or (
                re.search(r"\d\.$", candidate.strip()) and re.match(r"\s+\d", body[m.start() + 1 :])
            ):
                continue
            _push_segment(segments, candidate, body_start + cursor, line_start)
            cursor = m.start() + 1
        _push_segment(segments, body[cursor:], body_start + cursor, line_start)
    return segments


# ---------------------------------------------------------------------------
# Identification
# ---------------------------------------------------------------------------

MANDATORY = re.compile(
    r"\b(shall|must|is required to|are required to|required|mandatory|to be (?:provided|supplied|furnished|submitted|tested|carried out|designed|rated|made|used|installed|conforming)|will be required)\b",
    re.I,
)
RECOMMENDED = re.compile(r"\b(should|recommended|preferabl[ey]|desirable)\b", re.I)
PERMITTED = re.compile(r"\b(may|optional)\b", re.I)
# v2 (identify_v2): obligations without "shall" — "wires are to be …", "motors are to operate on …",
# "the Engineer will inspect …". Commercial "will" clauses are already removed by zoning.
MANDATORY_V2 = re.compile(r"\b(?:is|are)\s+to\s+(?:be\s+)?[a-z]{3,}|\bwill\s+(?:be\s+)?[a-z]{3,}", re.I)
CONFORMITY = re.compile(
    r"\b(conform\w*|comply\w*|complian\w*|as per|in accordance with|according to|confirming to)\b", re.I
)
ATTRIBUTE_LINE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 ()/&.,'-]{1,60}?)\s*(?::|=|–|-{1,2})\s+(?P<value>\S.*)$")
BOILERPLATE = re.compile(
    r"^(?:tender|bid|nit|e-?tender|date|dated|ref(?:erence)?\.?\s*no|page|signature|name of|address|phone|tel|fax|e-?mail|contact|sl\.?\s*no|s\.?\s*no|item\s+no|note)\b",
    re.I,
)
VAGUE = re.compile(
    r"\b(suitable|adequate|appropriate|good quality|best quality|standard make|reputed make|approved make|as required|as per requirement|energy[\s-]efficient|sufficient|high quality|proper|reliable|robust|latest technology|state[\s-]of[\s-]the[\s-]art|heavy duty|efficient|relevant (?:IS|standards?|codes?))\b",
    re.I,
)
# v2 zoning: text under these headings is bidding/commercial material, not specification.
EXCLUDED_ZONE = re.compile(
    r"instructions?\s+to\s+(?:bidders|tenderers)|invitation\s+for\s+bids|general\s+conditions|special\s+conditions|"
    r"conditions\s+of\s+contract|commercial\s+terms|terms\s+and\s+conditions|eligibility|qualification\s+criteria|"
    r"schedule\s+of\s+quantities|bill\s+of\s+quantities|approved\s+makes|price\s+bid|financial\s+bid|notice\s+inviting",
    re.I,
)
BOILERPLATE_V2 = re.compile(
    r"^(?:name\s+of\s+(?:the\s+)?work|estimated\s+cost|earnest\s+money|period\s+of\s+completion|last\s+date|"
    r"tender\s+(?:fee|no)|bid\s+security|subject\s*:|enquiry\s+no|notice\s+inviting|annexure)\b",
    re.I,
)
PLACEHOLDER = re.compile(r"\bto\s+be\s+(?:furnished|filled|quoted|specified|offered)\s+by\s+the\s+(?:bidder|tenderer|supplier)", re.I)
TABLE_ROW = re.compile(r"(?:[^|]*\|){2,}")
SUITABLE_FOR = re.compile(r"\bsuitable\s+for\s+(?!.*\b(?:purpose|use|site|requirement)s?\b)", re.I)
VAGUE_V2_EXTRA = re.compile(r"\bas\s+(?:low|high|far|much)\s+as\s+possible\b", re.I)

STANDARDS_HEADING = re.compile(r"\b(standards?|codes?|references?|specifications? applicable|applicable)\b", re.I)


@dataclass
class Candidate:
    modality: str
    confidence: float
    signals: list[str]


def identify(text: str, has_value: bool, has_reference: bool, in_standards_section: bool) -> Optional[Candidate]:
    if len(text) < 8 or BOILERPLATE.search(text):
        return None
    words = len(text.split())
    m = MANDATORY.search(text)
    if m:
        return Candidate("mandatory", 0.95 if has_value or has_reference else 0.85, [f'deontic cue "{m.group(0)}"'])
    if current().identify_v2:
        m = MANDATORY_V2.search(text)
        if m:
            return Candidate("mandatory", 0.9 if has_value or has_reference else 0.8, [f'obligation cue "{m.group(0)}"'])
    m = RECOMMENDED.search(text)
    if m:
        return Candidate("recommended", 0.75, [f'advisory cue "{m.group(0)}"'])
    attr = ATTRIBUTE_LINE.match(text)
    if attr and (has_value or has_reference):
        return Candidate("declarative", 0.8, [f'attribute line "{attr.group("key").strip()}: …" with a value'])
    conformity = CONFORMITY.search(text)
    if has_reference and (conformity or in_standards_section):
        return Candidate(
            "declarative",
            0.75,
            [
                "standard listed under an applicable-standards heading"
                if in_standards_section
                else f'conformity cue "{conformity.group(0) if conformity else ""}"'
            ],
        )
    m = PERMITTED.search(text)
    if m and has_value:
        return Candidate("permitted", 0.55, [f'permissive cue "{m.group(0)}" with a value'])
    if has_value and words <= 16:
        return Candidate("declarative", 0.6, ["short specification fragment with a measurable value"])
    return None


# ---------------------------------------------------------------------------
# Attribute assembly
# ---------------------------------------------------------------------------

_MENTION_RES: dict[str, re.Pattern[str]] = {}


def _mention_re(cue: str) -> re.Pattern[str]:
    pattern = _MENTION_RES.get(cue)
    if pattern is None:
        pattern = _MENTION_RES[cue] = re.compile(r"\b" + re.escape(cue) + r"\b")
    return pattern


TEST_MENTION = re.compile(r"\b(test|tested|testing|tests|verification|verified|inspection|inspected)\b")
_CABLE_CONTEXT = re.compile(r"\b(cable|conductor|wire|wiring)\b", re.I)


def build_attributes(
    text: str,
    base: int,
    quantities: list[Quantity],
    entities: list[Entity],
    references: list[StandardReference],
    signals: list[str],
) -> list[Attribute]:
    attributes: list[Attribute] = []
    lower = text.lower()

    for q in quantities:
        param = infer_parameter(text, q, base)
        if not param:
            continue
        attributes.append(Attribute(param.key, q, None))
        signals.append(param.signal)
        # "415 V ±10 %" also states the permissible variation.
        if q.comparator == "tolerance" and q.tolerance is not None and q.unit != "%":
            variation = (
                "frequency_variation"
                if param.key == "frequency"
                else "voltage_variation"
                if param.key == "rated_voltage"
                else None
            )
            if variation:
                pct = float(f"{q.tolerance * 100:.4f}")
                attributes.append(
                    Attribute(
                        variation,
                        dataclasses.replace(
                            q, value=pct, min=pct, max=pct, unit="%", dimension="percent", comparator="tolerance"
                        ),
                        None,
                    )
                )

    cable_context = bool(_CABLE_CONTEXT.search(text))
    for e in entities:
        if e.kind == "ip_rating":
            attributes.append(Attribute("ip_rating", None, e.value))
        elif e.kind == "concrete_grade":
            # "M25" designates a characteristic strength of 25 MPa: a specific value.
            mpa = float(e.value[1:])
            attributes.append(
                Attribute(
                    "concrete_grade",
                    Quantity(e.raw, e.span, mpa, mpa, mpa, "MPa", "pressure", "eq", None),
                    e.value,
                )
            )
        elif e.kind == "steel_grade":
            attributes.append(Attribute("steel_grade", None, e.value))
        elif e.kind == "material":
            if cable_context and e.value in ("copper", "aluminium"):
                attributes.append(Attribute("conductor_material", None, e.value))
            elif cable_context and e.value in ("PVC", "XLPE"):
                attributes.append(Attribute("insulation_material", None, e.value))
        elif e.kind == "certification":
            attributes.append(Attribute("conformity_evidence", None, e.value))
        elif e.kind == "test":
            attributes.append(
                Attribute("test_method", None, ", ".join(r.designation for r in references) if references else None)
            )

    for tp in extract_text_parameters(text):
        attributes.append(Attribute(tp.parameter, None, tp.value))

    # v2: "Routine verification … in accordance with IS/IEC 61439-1" states its test method.
    if current().attributes_v2 and references and TEST_MENTION.search(lower):
        if not any(a.parameter == "test_method" and a.text for a in attributes):
            attributes = [a for a in attributes if a.parameter != "test_method"]
            attributes.append(Attribute("test_method", None, ", ".join(r.designation for r in references)))

    # Parameters mentioned without any value → recorded as unvalued attributes
    # so gap detection can report them as insufficiently specified.
    valued = {a.parameter for a in attributes}
    for param in PARAMETERS:
        if param.key in valued or not param.mention_cues:
            continue
        cue = next((c for c in param.mention_cues if _mention_re(c).search(lower)), None)
        if cue:
            attributes.append(Attribute(param.key, None, None))
            signals.append(f'mentions {param.key} ("{cue}") without a value')
    return _dedupe_attributes(attributes)


def _dedupe_attributes(attributes: list[Attribute]) -> list[Attribute]:
    seen: set[str] = set()
    out: list[Attribute] = []
    for a in attributes:
        key = f"{a.parameter}|{a.text or ''}|{a.quantity.span.start if a.quantity else ''}"
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class Fragment:
    """A free-text fragment (e.g. a search query) structured like a requirement."""

    text: str
    terms: list[str]
    attributes: list[Attribute]
    category: str
    references: list[StandardReference]


def structure_fragment(text: str) -> Fragment:
    quantities = extract_quantities(text)
    references = extract_standard_references(text)
    entities = extract_entities(text)
    attributes = build_attributes(text, 0, quantities, entities, references, [])
    category = classify_requirement(text, quantities, entities, attributes).category
    return Fragment(text, extract_product_terms(text), attributes, category, references)


def extract_requirements(
    text: str, sections: list[Section], page_at: Callable[[int], Optional[int]]
) -> list[StructuredRequirement]:
    out: list[StructuredRequirement] = []
    seen_text: set[str] = set()
    heading_starts = {s.span.start for s in sections if s.heading}
    headed = [s for s in sections if s.heading]

    cfg = current()
    for seg in segment(text):
        # A heading line is context, never a requirement.
        if seg.line_start in heading_starts or seg.start in heading_starts:
            sec = next((s for s in sections if s.span.start in (seg.line_start, seg.start)), None)
            if sec and sec.heading and len(seg.text) <= len(sec.heading) + 2:
                continue
            # v3.1: a labelled heading ("SECTION IV – 11 kV POWER CABLES") is longer than its title.
            if cfg.identify_v2 and sec and sec.heading and seg.start + len(seg.text) <= sec.span.end + 1:
                continue
        quantities = extract_quantities(seg.text, seg.start)
        references = extract_standard_references(seg.text, seg.start)
        entities = extract_entities(seg.text, seg.start)
        text_params = extract_text_parameters(seg.text)
        has_value = (
            len(quantities) > 0 or any(e.kind not in ("test", "material") for e in entities) or len(text_params) > 0
        )
        section, label = locate(sections, seg.start)
        prior_headings = [s for s in headed if s.span.start <= seg.start]
        heading = prior_headings[-1].heading if prior_headings else ""
        zone = "specification"
        if cfg.zoning:
            if heading and EXCLUDED_ZONE.search(heading):
                continue  # instructions to bidders, commercial conditions, BOQ, approved makes …
            if BOILERPLATE_V2.search(seg.text) or PLACEHOLDER.search(seg.text) or TABLE_ROW.match(seg.text):
                continue
        candidate = identify(seg.text, has_value, len(references) > 0, bool(STANDARDS_HEADING.search(heading)))
        if not candidate:
            continue

        normalized = re.sub(r"\s+", " ", seg.text.lower())
        if normalized in seen_text:
            continue
        seen_text.add(normalized)

        signals = list(candidate.signals)
        attributes = build_attributes(seg.text, seg.start, quantities, entities, references, signals)
        cls = classify_requirement(seg.text, quantities, entities, attributes)
        vague_match = VAGUE.search(seg.text)
        if cfg.reasoning_v31 and vague_match and vague_match.group(0).lower() == "approved make":
            # "of approved make" points to the tender's list of approved makes; it is not vague.
            vague_match = next((m for m in VAGUE.finditer(seg.text) if m.group(0).lower() != "approved make"), None)
        if cfg.vague_version >= 2:
            if vague_match and vague_match.group(0).lower() == "suitable" and SUITABLE_FOR.search(seg.text):
                vague_match = None  # "suitable for star-delta starting" names what it is suitable for
            vague_match = vague_match or VAGUE_V2_EXTRA.search(seg.text)
        vague = (
            bool(vague_match)
            and not quantities
            and not references
            and not text_params
            and not any(e.kind in ("ip_rating", "concrete_grade", "steel_grade") for e in entities)
        )
        if vague and vague_match:
            signals.append(f'vague wording "{vague_match.group(0)}" without a measurable value')

        out.append(
            StructuredRequirement(
                id=f"req-{len(out) + 1}",
                text=seg.text,
                span=TextSpan(seg.start, seg.start + len(seg.text)),
                section_id=section.id if section else None,
                section_label=label,
                page=page_at(seg.start),
                modality=candidate.modality,
                category=cls.category,
                category_scores=cls.scores,
                quantities=quantities,
                references=references,
                entities=entities,
                attributes=attributes,
                terms=_terms(seg.text, heading if cfg.product_terms_v2 else ""),
                vague=vague,
                provenance=provenance(
                    "nlp.requirements",
                    "rule",
                    candidate.confidence,
                    [
                        *signals,
                        f"category {cls.category} (confidence {cls.confidence:.2f}, {cls.method})",
                        *([f"zone {zone} under heading '{heading[:60]}'"] if cfg.zoning and heading else []),
                    ],
                ),
            )
        )
    return out


def _terms(text: str, heading: str) -> list[str]:
    """Product terms of the requirement; v2 inherits its section heading's products when it names none."""
    terms = extract_product_terms(text)
    if not terms and heading:
        terms = extract_product_terms(heading)
    return terms
