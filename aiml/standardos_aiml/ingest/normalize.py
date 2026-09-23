"""Text normalisation.

Runs on every page before section and requirement detection so that
downstream regexes see one consistent character set.
"""

from __future__ import annotations

import math
import re
import unicodedata

CHAR_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile("º"), "°"),  # masculine ordinal is often typed for the degree sign; NFKC would turn it into "o"
    (re.compile("−"), "-"),  # minus sign
    (re.compile("[‒—―]"), "–"),  # dash variants -> en dash
    (re.compile("[‘’‚′]"), "'"),
    (re.compile("[“”„″]"), '"'),
    (re.compile("[•●▪◦‣⁃]"), "•"),
    (re.compile("\t"), " "),
    (re.compile("[  -​  　]"), " "),
    (re.compile("­"), ""),  # soft hyphen
]


def normalize_characters(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text)
    for pattern, replacement in CHAR_MAP:
        text = pattern.sub(replacement, text)
    # NFKC folds ligatures, full-width forms and compatibility digits, but also
    # turns "²" into "2"; the unit table accepts both spellings.
    return unicodedata.normalize("NFKC", text)


ENUMERATOR = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]?\s|\(?[a-z]\)\s|\(?[ivx]{1,4}\)\s|•|-\s|\*\s)", re.I)
JOIN_TAIL = re.compile(
    r"(?:[,(–-]|\b(?:and|or|of|the|to|with|in|for|at|by|as|per|than|from|a|an|shall|be|is|are|not)\s*)$", re.I
)


def reflow_lines(text: str) -> str:
    """Join PDF line breaks that fall mid-sentence, keeping list items and headings apart."""
    out: list[str] = []
    for raw in text.split("\n"):
        line = re.sub(r" {2,}", " ", raw).strip()
        prev = out[-1] if out else ""
        if not line:
            out.append("")
            continue
        if prev:
            # Dehyphenate words split across lines: "insu-" + "lation".
            if re.search(r"[a-z]-$", prev) and re.match(r"[a-z]", line):
                out[-1] = prev[:-1] + line
                continue
            continues = bool(re.match(r"[a-z(]", line)) or (
                bool(JOIN_TAIL.search(prev)) and not ENUMERATOR.search(line)
            )
            if continues and not ENUMERATOR.search(line):
                out[-1] = f"{prev} {line}"
                continue
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def _is_page_counter(line: str) -> bool:
    return bool(
        re.match(r"^\s*(?:page\s*)?\d+\s*(?:of|/)\s*\d+\s*$", line, re.I)
        or re.match(r"^\s*-?\s*page\s+\d+\s*-?\s*$", line, re.I)
    )


def _shape(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip())


def strip_repeated_lines(pages: list[str]) -> list[str]:
    """Remove running headers/footers that repeat on most pages, and page counters."""
    if len(pages) < 3:
        return ["\n".join(l for l in p.split("\n") if not _is_page_counter(l)) for p in pages]
    counts: dict[str, int] = {}
    for page in pages:
        seen = {s for s in (_shape(l) for l in page.split("\n")) if s}
        for line in seen:
            counts[line] = counts.get(line, 0) + 1
    threshold = math.ceil(len(pages) * 0.6)
    repeated = {line for line, n in counts.items() if n >= threshold and len(line) < 120}
    return [
        "\n".join(l for l in page.split("\n") if not _is_page_counter(l) and _shape(l) not in repeated)
        for page in pages
    ]
