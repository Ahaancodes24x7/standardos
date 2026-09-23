"""Fielded BM25 over clauses, followed by an interpretable feature re-ranker."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from typing import Iterable, Optional, Protocol

from ..nlp.entities import PRODUCT_TERMS, extract_product_terms
from ..nlp.parameters import parameter_label
from ..provenance import clamp01, fmt_num, js_round, provenance
from ..types import Attribute, Corpus, CorpusClause, CorpusStandard, RetrievalHit
from .resolve import ResolvedReference, StandardResolver
from .text import synonyms_of, tokenize

_TEST_WORD = re.compile(r"\btest", re.I)

K1 = 1.2
B = 0.75

# Field weights: a clause document also carries its standard's title,
# keywords and scope, so a clause about "tests" in a cable standard is found
# by a query about cables.
FIELD_WEIGHTS = {"clause_text": 1.0, "heading": 1.5, "title": 1.2, "keywords": 1.5, "scope": 0.6, "designation": 2.0}


@dataclass(frozen=True)
class RetrievalOptions:
    expansion: bool = False  # use the domain thesaurus for query expansion
    document_context: bool = True  # add the document's dominant product terms to every query
    rerank: bool = True  # apply the feature re-ranker; when False, rank by BM25 only
    min_confidence: float = 0.35  # hits below this confidence are not returned as mappings
    top_k: int = 5


# Thesaurus expansion is off by default: it lowered R@1 on every split in the
# ablation (see aiml/eval/results/latest.md). It stays available for experiments.
DEFAULT_RETRIEVAL = RetrievalOptions()

# Re-ranker weights, set on the dev split of eval/datasets/retrieval.json.
# They are deliberately few and interpretable.
RERANK_WEIGHTS = {
    "bm25": 0.45,
    "clause_parameter": 0.2,
    "standard_parameter": 0.1,
    "product": 0.2,
    "context_product": 0.08,
    "document_cited": 0.12,
    "explicit": 0.6,
}
# Sum of the non-explicit weights; raw scores are divided by it so confidence lies in [0, 1].
MAX_FEATURE_SCORE = (
    RERANK_WEIGHTS["bm25"]
    + RERANK_WEIGHTS["clause_parameter"]
    + RERANK_WEIGHTS["standard_parameter"]
    + RERANK_WEIGHTS["product"]
    + RERANK_WEIGHTS["context_product"]
    + RERANK_WEIGHTS["document_cited"]
)


class RequirementLike(Protocol):
    text: str
    terms: list[str]
    attributes: list[Attribute]
    category: str


@dataclass
class _Doc:
    clause: CorpusClause
    standard: CorpusStandard
    tf: dict[str, float]
    length: float


@dataclass
class _Ranked:
    doc: _Doc
    score: float
    matched: list[tuple[str, float]]


@dataclass
class _Scored:
    clause: CorpusClause
    standard: CorpusStandard
    raw: float
    final: float
    bm25: float
    signals: list[str]
    clause_param_hit: list[str]
    product_hit: list[str]
    explicit: bool
    matched: list[tuple[str, float]]


class StandardsIndex:
    def __init__(self, corpus: Corpus) -> None:
        self.corpus = corpus
        self.resolver = StandardResolver(corpus)
        self._product_forms: dict[str, list[str]] = dict(PRODUCT_TERMS)
        self._docs: list[_Doc] = []
        self._doc_by_clause: dict[str, _Doc] = {}
        self._df: dict[str, int] = {}
        for standard in corpus.standards:
            for clause in standard.clauses:
                tf: dict[str, float] = {}

                def add(text: str, weight: float) -> None:
                    for token in tokenize(text):
                        tf[token] = tf.get(token, 0) + weight

                add(clause.text, FIELD_WEIGHTS["clause_text"])
                add(clause.heading, FIELD_WEIGHTS["heading"])
                add(standard.title, FIELD_WEIGHTS["title"])
                add(" ".join(standard.keywords), FIELD_WEIGHTS["keywords"])
                add(standard.scope, FIELD_WEIGHTS["scope"])
                add(standard.designation, FIELD_WEIGHTS["designation"])
                doc = _Doc(clause, standard, tf, sum(tf.values()))
                self._docs.append(doc)
                self._doc_by_clause[clause.id] = doc
                for token in tf:
                    self._df[token] = self._df.get(token, 0) + 1
        self._avg_length = sum(d.length for d in self._docs) / max(1, len(self._docs))
        self._idf_cache: dict[str, float] = {}

    def _idf(self, token: str) -> float:
        cached = self._idf_cache.get(token)
        if cached is None:
            n = len(self._docs)
            df = self._df.get(token, 0)
            cached = self._idf_cache[token] = math.log(1 + (n - df + 0.5) / (df + 0.5))
        return cached

    def build_query(
        self, text: str, extra_terms: Iterable[str], context_terms: Iterable[str], options: RetrievalOptions
    ) -> dict[str, float]:
        """Weighted query terms for a requirement; weights reflect the source of each term."""
        query: dict[str, float] = {}

        def bump(token: str, weight: float) -> None:
            query[token] = max(query.get(token, 0), weight)

        for token in tokenize(text):
            bump(token, 1)
        for term in extra_terms:
            for token in tokenize(term):
                bump(token, 0.8)
        if options.document_context:
            for term in context_terms:
                for token in tokenize(term):
                    bump(token, 0.3)
        if options.expansion:
            for token, weight in list(query.items()):
                for syn in synonyms_of(token):
                    bump(syn, weight * 0.5)
        return query

    def bm25(self, query: dict[str, float]) -> list[_Ranked]:
        results: list[_Ranked] = []
        for doc in self._docs:
            score = 0.0
            matched: list[tuple[str, float]] = []
            for token, q_weight in query.items():
                tf = doc.tf.get(token)
                if not tf:
                    continue
                contribution = (
                    q_weight
                    * self._idf(token)
                    * ((tf * (K1 + 1)) / (tf + K1 * (1 - B + (B * doc.length) / self._avg_length)))
                )
                score += contribution
                matched.append((token, contribution))
            if score > 0:
                results.append(_Ranked(doc, score, sorted(matched, key=lambda m: -m[1])))
        return sorted(results, key=lambda r: -r.score)

    def _standard_matches_product(self, standard: CorpusStandard, product: str) -> bool:
        forms = [product, *self._product_forms.get(product, [])]
        haystack = f"{standard.title} {' '.join(standard.keywords)} {standard.scope}".lower()
        return any(form in haystack for form in forms)

    def retrieve(
        self,
        requirement: RequirementLike,
        resolved: list[ResolvedReference],
        context_terms: list[str],
        options: RetrievalOptions = DEFAULT_RETRIEVAL,
        document_cited_ids: Optional[set[str]] = None,
    ) -> list[RetrievalHit]:
        """Retrieve and re-rank standards/clauses for one requirement.

        Explicitly cited standards (resolved references) are always included
        and ranked first.
        """
        document_cited_ids = document_cited_ids or set()
        # Only parameters the requirement actually states count as retrieval
        # evidence; a bare mention ("cover to reinforcement") is too weak —
        # except a test mention, which is how test-method standards are found.
        params = list(
            dict.fromkeys(
                a.parameter for a in requirement.attributes if a.quantity or a.text or a.parameter == "test_method"
            )
        )
        param_labels = [parameter_label(p) for p in params]
        query = self.build_query(requirement.text, [*requirement.terms, *param_labels], context_terms, options)
        ranked = self.bm25(query)[:40]
        max_score = ranked[0].score if ranked else 1
        explicit_ids = list(dict.fromkeys(r.standard_id for r in resolved if r.standard_id))
        mentions_testing = requirement.category == "testing" or bool(_TEST_WORD.search(requirement.text))

        # Make sure every clause of an explicitly cited standard is scored.
        candidates: dict[str, _Ranked] = {r.doc.clause.id: r for r in ranked}
        for standard_id in explicit_ids:
            std = self.resolver.get(standard_id)
            for clause in std.clauses if std else []:
                if clause.id not in candidates:
                    doc = self._doc_by_clause.get(clause.id)
                    if doc:
                        candidates[clause.id] = _Ranked(doc, 0, [])

        scored: list[_Scored] = []
        for item in candidates.values():
            clause, standard = item.doc.clause, item.doc.standard
            bm25n = item.score / max_score
            clause_params = {c.parameter for c in clause.constraints} | {
                i.parameter for i in standard.checklist if i.clause_id == clause.id
            }
            std_params = {k.parameter for c in standard.clauses for k in c.constraints} | {
                i.parameter for i in standard.checklist
            }
            # A test-method standard is what a test requirement's "test_method"
            # parameter refers to, even though it carries no checklist of its own.
            if standard.kind == "test_method":
                clause_params.add("test_method")
                std_params.add("test_method")
            clause_param_hit = [p for p in params if p in clause_params]
            std_param_hit = [p for p in params if p in std_params]
            product_hit = [t for t in requirement.terms if self._standard_matches_product(standard, t)]
            context_hit = (
                [t for t in context_terms if self._standard_matches_product(standard, t)]
                if options.document_context
                else []
            )
            explicit = standard.id in explicit_ids
            doc_cited = options.document_context and not explicit and standard.id in document_cited_ids

            signals: list[str] = []
            if options.rerank:
                final = (
                    RERANK_WEIGHTS["bm25"] * bm25n
                    + RERANK_WEIGHTS["clause_parameter"] * (1 if clause_param_hit else 0)
                    + RERANK_WEIGHTS["standard_parameter"] * (1 if std_param_hit else 0)
                    + RERANK_WEIGHTS["product"] * (1 if product_hit else 0)
                    + RERANK_WEIGHTS["context_product"] * (1 if context_hit else 0)
                    + RERANK_WEIGHTS["document_cited"] * (1 if doc_cited else 0)
                ) / MAX_FEATURE_SCORE + RERANK_WEIGHTS["explicit"] * (1 if explicit else 0)
                if doc_cited:
                    signals.append("standard is cited elsewhere in the document")
                if standard.status == "superseded" and not explicit:
                    final *= 0.5
                    signals.append("superseded standard down-weighted")
                if standard.kind == "test_method" and not mentions_testing and not explicit:
                    final *= 0.6
                    signals.append("test-method standard down-weighted for a non-testing requirement")
                # Out of domain: the requirement/document names products and this standard covers none of them.
                known_products = len(requirement.terms) > 0 or (options.document_context and len(context_terms) > 0)
                if known_products and not product_hit and not context_hit and not explicit and not doc_cited:
                    final *= 0.6
                    signals.append("standard's scope covers none of the products in the requirement or document")
            else:
                final = bm25n
            if item.matched:
                terms = ", ".join(f'"{t}"' for t, _ in item.matched[:4])
                signals.insert(0, f"BM25 {_fmt2(item.score)} on {terms}")
            if clause_param_hit:
                signals.append(f"clause governs {', '.join(parameter_label(p) for p in clause_param_hit)}")
            elif std_param_hit:
                signals.append(f"standard covers {', '.join(parameter_label(p) for p in std_param_hit)}")
            if product_hit:
                signals.append(f'product "{product_hit[0]}" is in the standard\'s scope')
            elif context_hit:
                signals.append(f'document is about "{context_hit[0]}", which is in the standard\'s scope')
            if explicit:
                signals.append("standard is cited explicitly in the requirement")

            # `raw` keeps explicit citations ranked above everything else; confidence is clamped.
            scored.append(
                _Scored(
                    clause,
                    standard,
                    final,
                    clamp01(final),
                    item.score,
                    signals,
                    clause_param_hit,
                    product_hit,
                    explicit,
                    item.matched,
                )
            )

        # Best clause per standard, then rank standards.
        best: dict[str, _Scored] = {}
        for s in scored:
            prev = best.get(s.standard.id)
            if prev is None or s.raw > prev.raw:
                best[s.standard.id] = s
        ranked_standards = sorted(best.values(), key=lambda s: -s.raw)
        kept = [s for s in ranked_standards if s.final >= options.min_confidence or s.explicit][: options.top_k]
        return [
            RetrievalHit(
                standard_id=s.standard.id,
                clause_id=s.clause.id,
                score=js_round(s.bm25, 4),
                confidence=js_round(s.final),
                explanation=_explain(s),
                provenance=provenance(
                    "standards.rerank" if options.rerank else "standards.retrieval",
                    "rerank" if options.rerank else "bm25",
                    s.final,
                    s.signals,
                ),
            )
            for s in kept
        ]

    def rank_clauses(self, text: str, options: RetrievalOptions = DEFAULT_RETRIEVAL) -> list[str]:
        """Clause-level ranking for evaluation (all clauses, not collapsed per standard)."""
        query = self.build_query(text, extract_product_terms(text), [], options)
        return [r.doc.clause.id for r in self.bm25(query)]


def _fmt2(value: float) -> str:
    return fmt_num(js_round(value, 2))


def _explain(s: _Scored) -> str:
    parts: list[str] = []
    if s.explicit:
        parts.append(f"The requirement cites {s.standard.number} directly.")
    if s.product_hit:
        parts.append(
            f"The {s.product_hit[0]} described in the requirement falls within the scope of {s.standard.number}."
        )
    if s.clause_param_hit:
        governed = " and ".join(parameter_label(p).lower() for p in s.clause_param_hit)
        parts.append(f'The clause "{s.clause.heading}" governs {governed}, which the requirement specifies.')
    terms = [t for t, _ in s.matched[:3]]
    if terms:
        parts.append(f"Shared technical terms: {', '.join(terms)}.")
    if not parts:
        parts.append(f"Lexical similarity with {s.standard.number}.")
    return " ".join(parts)


def document_context_terms(requirements: Iterable[RequirementLike]) -> list[str]:
    """Dominant product terms of a document: terms in ≥ 2 requirements, else the most frequent."""
    counts: dict[str, int] = {}
    for r in requirements:
        for t in dict.fromkeys(r.terms):
            counts[t] = counts.get(t, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    frequent = [t for t, n in ranked if n >= 2]
    return (frequent if frequent else [t for t, _ in ranked[:2]])[:4]


def with_options(options: RetrievalOptions, **changes: object) -> RetrievalOptions:
    return replace(options, **changes)  # type: ignore[arg-type]
