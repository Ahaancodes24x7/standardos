"""Pattern-based relationship extraction.

For each standard reference in a sentence, the cue phrase immediately
governing it decides the relation type. Cues are checked from most to least
specific; a bare mention with no cue is REFERENCES. This is used both to build
graph edges from clause text and to link procurement requirements to the
standards they invoke.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..nlp.entities import extract_standard_references
from ..provenance import provenance
from ..types import Corpus, CorpusRelationship, Provenance, StandardReference
from .resolve import StandardResolver


@dataclass(frozen=True)
class _Cue:
    type: str
    pattern: re.Pattern[str]
    label: str


# Matched against the text between the previous reference (or sentence start) and this reference.
CUES: list[_Cue] = [
    # "refer to X" is a pointer, not an obligation; checked first so later cues in the window don't override it.
    _Cue("REFERENCES", re.compile(r"\b(refer\w*(?:\s+to)?|based on|reference to)\s*$", re.I), "pointer cue"),
    _Cue(
        "SUPERSEDES",
        re.compile(
            r"\b(supersed\w*|replac\w*|in place of|in lieu of|revis\w* (?:of|into|as)|consolidat\w*|(?:now\s+)?covered by|now specified by)\b",
            re.I,
        ),
        "supersession cue",
    ),
    _Cue("AMENDED_BY", re.compile(r"\b(amend\w*|amendment no\.?)\b", re.I), "amendment cue"),
    _Cue(
        "TESTED_BY",
        re.compile(
            r"\b(test\w*|tested|methods? of (?:test|sampling)|examin\w*|measur\w*|verif\w*|determined|sampl\w*|analys\w*)\b"
            r"[^.;]{0,80}?\b(?:in accordance with|as per|according to|per|following|follows?|by|to|using|of|(?:as\s+)?(?:specified|given|described)\s+in|in)"
            r"\s*(?:the\s+)?(?:relevant\s+)?(?:parts?\s+of\s+)?(?:(?:tests?|methods?)\s+(?:of|in)\s+)?"
            r"(?:[\w\s,-]{0,40}?(?:chiefly|namely|such as|e\.g\.|for example)\s+(?:the\s+)?)?$",
            re.I,
        ),
        "test-method cue",
    ),
    _Cue(
        "REQUIRES",
        re.compile(
            r"\b(shall conform\w* to|conform\w* to|shall comply with|comply\w* with|complying with|shall meet(?: the requirements of)?"
            r"|in accordance with|as per|read (?:together|in conjunction) with|designed (?:to|in accordance with)|shall be to|per)"
            r"\s*(?:the\s+)?(?:relevant\s+)?(?:requirements\s+of\s+)?(?:parts?\s+of\s+)?$",
            re.I,
        ),
        "conformity cue",
    ),
    _Cue("RELATED_TO", re.compile(r"\b(see also|related(?:\s+to)?|similar to|cf\.?)\s*$", re.I), "relatedness cue"),
]

_BOUNDARY = re.compile(r"[.;]\s+(?=[A-Z(])")
_ABBREV_END = re.compile(r"\b(?:No|Nos|Cl|Pt|Sec|e\.g|i\.e)\.$")
_COORDINATION = re.compile(r"(,|\band\b|\bor\b|/)")
_CONFORMITY_EXAMPLES = re.compile(
    r"\b(?:conform\w*|in accordance with|as per)\b[^.;]*\b(?:e\.g\.|for example|such as)\b", re.I
)


def _last_boundary(text: str) -> int:
    """Offset just after the last sentence/clause boundary in ``text`` ("No. 2" is not a boundary)."""
    last = -1
    for m in _BOUNDARY.finditer(text):
        if _ABBREV_END.search(text[: m.start() + 1]):
            continue
        last = m.end()
    return last


@dataclass
class ExtractedRelation:
    type: str
    reference: StandardReference
    cue: str
    provenance: Provenance


def extract_relations(text: str) -> list[ExtractedRelation]:
    """Relations stated in ``text`` toward the standards it references."""
    out: list[ExtractedRelation] = []
    window_start = 0
    for ref in extract_standard_references(text):
        # Window: text since the previous reference, cut at the last sentence/clause boundary.
        before = text[window_start : ref.span.start]
        boundary = _last_boundary(before)
        window = before[boundary:] if boundary >= 0 else before
        # Coordinated references ("IS 269 for cement, IS 383 for aggregates and IS 1786")
        # share the cue that governs the first one.
        inherited = len(out) > 0 and boundary < 0 and len(before) < 60 and bool(_COORDINATION.search(before))
        rel_type = "REFERENCES"
        cue = "bare mention"
        confidence = 0.6
        for candidate in CUES:
            m = candidate.pattern.search(window)
            if m:
                rel_type = candidate.type
                cue = f'{candidate.label} "{m.group(0).strip()[:40]}"'
                confidence = 0.6 if candidate.type == "RELATED_TO" else 0.8
                break
        if cue == "bare mention" and inherited:
            prev = out[-1]
            rel_type = prev.type
            cue = f"{prev.cue} (coordinated reference)"
            confidence = 0.7
        # Mentions in a list introduced with "for example" / "e.g." after a conformity cue.
        if cue == "bare mention" and _CONFORMITY_EXAMPLES.search(window):
            rel_type = "REQUIRES"
            cue = "conformity cue with examples"
            confidence = 0.7
        out.append(
            ExtractedRelation(
                rel_type,
                ref,
                cue,
                provenance("standards.relations", "rule", confidence, [cue, f"target {ref.designation}"]),
            )
        )
        window_start = ref.span.end
    return out


def extract_corpus_relationships(corpus: Corpus, resolver: StandardResolver) -> list[CorpusRelationship]:
    """Build graph edges from clause texts of the corpus.

    Returned edges carry method "extracted" so they can be evaluated against,
    or merged with, the curated edges. Self-references and unresolved targets
    are dropped.
    """
    out: list[CorpusRelationship] = []
    seen: set[str] = set()
    for std in corpus.standards:
        for clause in std.clauses:
            for rel in extract_relations(clause.text):
                resolved = resolver.resolve(rel.reference)
                if not resolved.standard_id or resolved.standard_id == std.id:
                    continue
                # "X replaces Y" in the text of X means X SUPERSEDES Y; "Y replaced by X" is stated in Y's own record.
                src, dst = std.id, resolved.standard_id
                if rel.type == "SUPERSEDES" and std.status == "superseded":
                    src, dst = dst, src
                key = f"{rel.type}|{src}|{dst}"
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    CorpusRelationship(
                        id=f"x-{len(out) + 1}",
                        type=rel.type,
                        from_id=src,
                        to_id=dst,
                        clause_id=clause.id,
                        confidence=rel.provenance.confidence * resolved.provenance.confidence,
                        method="extracted",
                        note=rel.cue,
                    )
                )
    return out
