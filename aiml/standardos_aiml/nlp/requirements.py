"""Requirement segmentation, identification and attribute assembly."""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from typing import Callable, Optional

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
            if ABBREVIATIONS.search(candidate) or (
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

    for seg in segment(text):
        # A heading line is context, never a requirement.
        if seg.line_start in heading_starts or seg.start in heading_starts:
            sec = next((s for s in sections if s.span.start in (seg.line_start, seg.start)), None)
            if sec and sec.heading and len(seg.text) <= len(sec.heading) + 2:
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
                terms=extract_product_terms(seg.text),
                vague=vague,
                provenance=provenance(
                    "nlp.requirements",
                    "rule",
                    candidate.confidence,
                    [*signals, f"category {cls.category} (confidence {cls.confidence:.2f})"],
                ),
            )
        )
    return out
