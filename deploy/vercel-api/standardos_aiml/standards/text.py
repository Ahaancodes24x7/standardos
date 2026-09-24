"""Tokenisation, light stemming and a domain thesaurus for retrieval."""

from __future__ import annotations

import re

STOPWORDS = set(
    "a an and are as at be been by for from has have in into is it its of on or shall should such that the their "
    "them then there these this those to under upon was were which will with within without all any each other "
    "than per not no only also may must can being both".split(" ")
)


def stem(token: str) -> str:
    """Minimal suffix stemmer: enough to conflate plurals and -ing/-ed forms in technical English."""
    if len(token) <= 3 or re.search(r"\d", token):
        return token
    if token.endswith("ies") and len(token) > 4:
        return f"{token[:-3]}y"
    if token.endswith("sses"):
        return token[:-2]
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4 and not token.endswith("eed"):
        return token[:-2]
    if token.endswith("s") and not re.search(r"(ss|us|is)$", token):
        return token[:-1]
    return token


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [stem(t) for t in _NON_ALNUM.sub(" ", text.lower()).split(" ") if len(t) > 1 and t not in STOPWORDS]


# Synonym groups. Chosen from terminology variation seen in Indian procurement
# documents ("earthing" vs "grounding", "panel" vs "switchboard"), which is the
# main paraphrase gap for a lexical retriever.
GROUPS: list[list[str]] = [
    ["earth", "earthing", "ground", "grounding", "earthed"],
    ["cable", "wire", "wir", "cord"],
    ["switchgear", "switchboard", "panel", "assembly", "assemblie", "controlgear", "pcc", "mcc", "board"],
    ["pump", "pumpset"],
    ["mcb", "breaker", "mccb", "acb"],
    ["rccb", "rcd", "elcb", "residual", "leakage"],
    ["enclosure", "ip", "ingress", "dust", "dustproof", "weatherproof", "splash"],
    ["concrete", "rcc", "pcc"],
    ["reinforcement", "rebar", "tmt", "hysd", "bar"],
    ["aggregate", "sand"],
    ["cement", "opc", "ppc"],
    ["potable", "drink", "drinking"],
    ["test", "testing", "inspection", "verification", "tested"],
    ["efficiency", "efficient", "ie2", "ie3", "ie4"],
    ["ambient", "temperature"],
    ["xlpe", "crosslink", "crosslinked"],
    ["borewell", "submersible"],
    ["coliform", "coli", "bacteriological", "microbiological"],
]

SYNONYMS: dict[str, list[str]] = {}
for _group in GROUPS:
    _stemmed = list(dict.fromkeys(stem(t) for t in _group))
    for _term in _stemmed:
        SYNONYMS[_term] = [t for t in _stemmed if t != _term]


def synonyms_of(token: str) -> list[str]:
    return SYNONYMS.get(token, [])
