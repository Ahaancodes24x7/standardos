from __future__ import annotations

import re
from typing import Callable, Optional

from ..types import Section, TextSpan

MODAL = re.compile(r"\b(shall|must|should|will|may|is required|are required)\b", re.I)
NUMBERED_HEADING = re.compile(r"^(?P<num>\d{1,2}(?:\.\d{1,3}){0,4})[.)]?\s+(?P<title>\S.{0,110})$")
LABELLED_HEADING = re.compile(
    r"^(?P<label>(?:section|chapter|part|annex(?:ure)?|appendix|schedule)\s+[\dA-Z]{1,4})\s*[:.–-]?\s*(?P<title>.{0,100})$",
    re.I,
)
_TITLE_SMALL_WORDS = re.compile(r"^(and|or|of|the|for|to|in|on|with|a|an)$")


def is_heading_text(title: str) -> bool:
    words = title.strip().split()
    if len(words) == 0 or len(words) > 12:
        return False
    if re.search(r"[.;]$", title.strip()):
        return False
    if MODAL.search(title):
        return False
    # "Rated voltage: 415 V" is a specification line, not a heading.
    if re.search(r":\s*\S", title) or re.search(r"\d(?:[.,]\d+)?\s*(?:[A-Za-z°%µ]|$)", title):
        return False
    return bool(re.match(r"[A-Z0-9]", title.strip()))


def is_unnumbered_heading(line: str) -> bool:
    trimmed = line.strip()
    if len(trimmed) < 3 or len(trimmed) > 80:
        return False
    if not is_heading_text(trimmed):
        return False
    if re.search(r":\s*\S", trimmed):  # "Voltage: 415 V" is an attribute line, not a heading
        return False
    letters = re.sub(r"[^A-Za-z]", "", trimmed)
    if len(letters) < 3:
        return False
    upper_ratio = len(re.sub(r"[^A-Z]", "", letters)) / len(letters)
    lower_words = [w for w in trimmed.split() if re.match(r"[a-z]", w) and not _TITLE_SMALL_WORDS.match(w)]
    return upper_ratio > 0.8 or len(lower_words) == 0


def detect_sections(text: str, page_at: Callable[[int], Optional[int]]) -> list[Section]:
    """Detect headings and numbered clauses.

    Numbered lines that read like a requirement ("4.2 The panel shall …") are
    recorded as clauses so requirements can cite their clause number; short
    title-like lines become headings that label the requirements beneath them.
    """
    sections: list[Section] = []
    offset = 0
    index = 0
    for line in text.split("\n"):
        start = offset
        offset += len(line) + 1
        trimmed = line.strip()
        if not trimmed:
            continue
        lead = len(line) - len(line.lstrip())
        span = TextSpan(start + lead, start + len(line))

        numbered = NUMBERED_HEADING.match(trimmed)
        if numbered:
            num = numbered.group("num")
            title = numbered.group("title")
            index += 1
            sections.append(
                Section(
                    id=f"sec-{index}",
                    number=num,
                    heading=title.strip() if is_heading_text(title) else "",
                    level=len(num.split(".")),
                    span=span,
                    page=page_at(span.start),
                )
            )
            continue
        labelled = LABELLED_HEADING.match(trimmed)
        if labelled and is_heading_text(trimmed):
            index += 1
            sections.append(
                Section(
                    id=f"sec-{index}",
                    number=labelled.group("label"),
                    heading=(labelled.group("title") or "").strip() or trimmed,
                    level=1,
                    span=span,
                    page=page_at(span.start),
                )
            )
            continue
        if is_unnumbered_heading(trimmed):
            index += 1
            sections.append(Section(f"sec-{index}", None, trimmed, 1, span, page_at(span.start)))
    return sections


def locate(sections: list[Section], offset: int) -> tuple[Optional[Section], Optional[str]]:
    """Label for the location of an offset: its own clause number plus the nearest heading."""
    clause: Optional[Section] = None
    heading: Optional[Section] = None
    for section in sections:
        if section.span.start > offset:
            break
        if section.heading:
            heading = section
        if section.number and re.match(r"\d", section.number):
            clause = section
    parts: list[str] = []
    if clause and not clause.heading:
        parts.append(f"Clause {clause.number}")
    if heading:
        parts.append(
            f"{heading.number} {heading.heading}"
            if heading.number and re.match(r"\d", heading.number)
            else heading.heading
        )
    return (clause or heading), (" · ".join(parts) if parts else None)
