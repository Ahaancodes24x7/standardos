"""Evaluation harness for the StandardOS intelligence pipeline.

Pure functions over the gold datasets in ``aiml/eval/datasets``; used by
``python -m eval.run`` (report) and ``aiml/tests/test_eval_gate.py`` (regression gate).
"""

from __future__ import annotations

import json
import math
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from standardos_aiml.nlp.entities import extract_standard_references
from standardos_aiml.nlp.requirements import structure_fragment
from standardos_aiml.pipeline import get_engine, run_pipeline
from standardos_aiml.standards.relations import extract_corpus_relationships, extract_relations
from standardos_aiml.standards.retrieval import RetrievalOptions
from standardos_aiml.standards.seed import seed_corpus
from standardos_aiml.types import Corpus, ReasoningFinding, StructuredRequirement

DATA = Path(__file__).parent / "datasets"
SPLITS = ("dev", "test", "heldout")


def load(name: str, data_dir: Path = DATA) -> dict[str, Any]:
    return json.loads((data_dir / name).read_text(encoding="utf-8"))


def in_split(split: str) -> Callable[[dict[str, Any]], bool]:
    return lambda item: split == "all" or item.get("split") == split


def r3(x: float) -> float:
    return math.floor(x * 1000 + 0.5) / 1000


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


@dataclass
class PRF:
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int


def prf(tp: int, fp: int, fn: int) -> PRF:
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return PRF(r3(precision), r3(recall), r3(f1), tp, fp, fn)


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def jaccard(a: str, b: str) -> float:
    A, B = set(norm(a).split()), set(norm(b).split())
    inter = len(A & B)
    return inter / ((len(A) + len(B) - inter) or 1)


def text_matches(predicted: str, gold: str) -> bool:
    return jaccard(predicted, gold) >= 0.6 or norm(gold) in norm(predicted) or norm(predicted) in norm(gold)


# ---------------------------------------------------------------------------
# Phase 1 — requirement extraction
# ---------------------------------------------------------------------------


def score_attributes(req: StructuredRequirement, gold: list[dict[str, Any]]) -> tuple[int, int, int]:
    """Attributes with a value count; value-less mentions are ignored.

    Only parameters present in gold are scored for precision.
    """
    valued = [a for a in req.attributes if a.quantity or a.text]
    tp = 0
    for g in gold:
        for a in valued:
            if a.parameter != g["parameter"]:
                continue
            if "value" in g:
                candidates = [
                    v for v in ((a.quantity.value, a.quantity.min, a.quantity.max) if a.quantity else ()) if v is not None
                ]
                if any(abs(v - g["value"]) <= abs(g["value"]) * 0.01 + 1e-9 for v in candidates):
                    tp += 1
                    break
            elif "text" in g:
                if (a.text or "").lower() == g["text"].lower():
                    tp += 1
                    break
            else:
                tp += 1
                break
    gold_params = {g["parameter"] for g in gold}
    fp = sum(1 for a in valued if a.parameter in gold_params) - tp
    return tp, max(0, fp), len(gold) - tp


def evaluate_requirements(
    corpus: Corpus, split: str, data_dir: Path = DATA, classify: Optional[Callable[[StructuredRequirement], str]] = None
) -> dict[str, Any]:
    """Identification P/R/F1, classification accuracy/macro-F1 and attribute P/R/F1.

    ``classify`` overrides the pipeline's category (used to score a learned classifier).
    """
    docs = [d for d in load("requirements.json", data_dir)["documents"] if in_split(split)(d)]
    tp = fp = fn = a_tp = a_fp = a_fn = 0
    confusion: list[tuple[str, str]] = []
    misses: list[str] = []
    spurious: list[str] = []
    for doc in docs:
        predicted = run_pipeline(doc["text"], corpus).requirements
        used: set[str] = set()
        for gold in doc["requirements"]:
            match = next((p for p in predicted if p.id not in used and text_matches(p.text, gold["text"])), None)
            if not match:
                fn += 1
                a_fn += len(gold["attributes"])
                misses.append(f"{doc['id']}: {gold['text'][:100]}")
                continue
            used.add(match.id)
            tp += 1
            confusion.append((gold["category"], classify(match) if classify else match.category))
            s_tp, s_fp, s_fn = score_attributes(match, gold["attributes"])
            a_tp, a_fp, a_fn = a_tp + s_tp, a_fp + s_fp, a_fn + s_fn
        extra = [p for p in predicted if p.id not in used]
        fp += len(extra)
        spurious += [f"{doc['id']}: {p.text[:100]}" for p in extra]
    labels = list(dict.fromkeys(label for pair in confusion for label in pair))
    per_class = [
        prf(
            sum(1 for g, p in confusion if g == label and p == label),
            sum(1 for g, p in confusion if g != label and p == label),
            sum(1 for g, p in confusion if g == label and p != label),
        ).f1
        for label in labels
    ]
    return {
        "documents": len(docs),
        "identification": asdict(prf(tp, fp, fn)),
        "classification": {
            "accuracy": r3(sum(1 for g, p in confusion if g == p) / (len(confusion) or 1)),
            "macroF1": r3(mean(per_class)),
            "n": len(confusion),
            "errors": [[g, p] for g, p in confusion if g != p],
        },
        "attributes": asdict(prf(a_tp, a_fp, a_fn)),
        "misses": misses,
        "spurious": spurious,
    }


# ---------------------------------------------------------------------------
# Phase 2 — retrieval, resolution, relations, graph
# ---------------------------------------------------------------------------

RETRIEVAL_ABLATIONS: dict[str, RetrievalOptions] = {
    "bm25": RetrievalOptions(expansion=False, document_context=False, rerank=False, min_confidence=0, top_k=10),
    "bm25+thesaurus": RetrievalOptions(expansion=True, document_context=False, rerank=False, min_confidence=0, top_k=10),
    "bm25+rerank": RetrievalOptions(expansion=False, document_context=False, rerank=True, min_confidence=0, top_k=10),
    "bm25+thesaurus+rerank": RetrievalOptions(
        expansion=True, document_context=False, rerank=True, min_confidence=0, top_k=10
    ),
}


def evaluate_retrieval(corpus: Corpus, split: str, options: RetrievalOptions, data_dir: Path = DATA) -> dict[str, Any]:
    queries = [q for q in load("retrieval.json", data_dir)["queries"] if in_split(split)(q)]
    index = get_engine(corpus).index
    r1, r3_, r5, rr, ndcg, c1, c3, crr = ([] for _ in range(8))
    misses: list[str] = []
    for q in queries:
        fragment = structure_fragment(q["text"])
        hits = index.retrieve(
            fragment, [], [], RetrievalOptions(options.expansion, options.document_context, options.rerank, 0, 10)
        )
        ranked = [h.standard_id for h in hits]
        relevant = [sid for sid, grade in q["standards"].items() if grade >= 2]
        first = next((i for i, sid in enumerate(ranked) if sid in relevant), -1)
        r1.append(1 if first == 0 else 0)
        r3_.append(1 if 0 <= first < 3 else 0)
        r5.append(1 if 0 <= first < 5 else 0)
        rr.append(1 / (first + 1) if first >= 0 else 0)
        if first != 0:
            misses.append(f"{q['id']}: expected {'|'.join(relevant)}, got {', '.join(ranked[:3])}")
        dcg = sum((2 ** q["standards"].get(sid, 0) - 1) / math.log2(i + 2) for i, sid in enumerate(ranked[:5]))
        ideal = sum(
            (2**g - 1) / math.log2(i + 2) for i, g in enumerate(sorted(q["standards"].values(), reverse=True)[:5])
        )
        ndcg.append(dcg / ideal if ideal else 0)
        # Clause level: rank all clauses (not collapsed per standard) for BM25-only configurations.
        clauses = [h.clause_id for h in hits] if options.rerank else index.rank_clauses(q["text"], options)
        first_clause = next((i for i, cid in enumerate(clauses) if cid in q["clauses"]), -1)
        c1.append(1 if first_clause == 0 else 0)
        c3.append(1 if 0 <= first_clause < 3 else 0)
        crr.append(1 / (first_clause + 1) if first_clause >= 0 else 0)
    return {
        "queries": len(queries),
        "standard": {
            "recallAt1": r3(mean(r1)),
            "recallAt3": r3(mean(r3_)),
            "recallAt5": r3(mean(r5)),
            "mrr": r3(mean(rr)),
            "ndcgAt5": r3(mean(ndcg)),
        },
        "clause": {"recallAt1": r3(mean(c1)), "recallAt3": r3(mean(c3)), "mrr": r3(mean(crr))},
        "misses": misses,
    }


def evaluate_resolution(corpus: Corpus, split: str, data_dir: Path = DATA) -> dict[str, Any]:
    cases = [c for c in load("resolution.json", data_dir)["cases"] if in_split(split)(c)]
    index = get_engine(corpus).index
    id_ok = edition_ok = 0
    errors: list[str] = []
    for c in cases:
        refs = extract_standard_references(c["text"])
        resolved = index.resolver.resolve(refs[0]) if refs else None
        sid = resolved.standard_id if resolved else None
        edition = resolved.edition if resolved else "unknown"
        if sid == c["expected"]:
            id_ok += 1
        else:
            errors.append(f"{c['id']}: \"{c['text']}\" → {sid} (expected {c['expected']})")
        if edition == c["edition"]:
            edition_ok += 1
        else:
            errors.append(f"{c['id']}: edition {edition} (expected {c['edition']})")
    return {
        "cases": len(cases),
        "accuracy": r3(id_ok / (len(cases) or 1)),
        "editionAccuracy": r3(edition_ok / (len(cases) or 1)),
        "errors": errors,
    }


def evaluate_relations(split: str, data_dir: Path = DATA) -> dict[str, Any]:
    sentences = [s for s in load("relations.json", data_dir)["sentences"] if in_split(split)(s)]
    tp = fp = fn = typed = 0
    errors: list[str] = []
    for s in sentences:
        gold = [tuple(r) for r in s["relations"]]
        for rel in extract_relations(s["text"]):
            pair = (rel.type, rel.reference.designation)
            if pair in gold:
                tp += 1
                gold.remove(pair)
            else:
                fp += 1
                if any(gd == pair[1] for _, gd in s["relations"]):
                    typed += 1
                errors.append(
                    f"{s['id']}: predicted {pair[0]} {pair[1]}; gold {', '.join(' '.join(r) for r in s['relations'])}"
                )
        fn += len(gold)
    return {
        "sentences": len(sentences),
        "typedRelation": asdict(prf(tp, fp, fn)),
        "wrongTypeOnCorrectTarget": typed,
        "errors": errors,
    }


def evaluate_graph_construction(corpus: Corpus) -> dict[str, Any]:
    """Graph construction: edges extracted from clause text vs the curated graph."""
    index = get_engine(corpus).index
    extracted = extract_corpus_relationships(corpus, index.resolver)

    def key(r: Any) -> str:
        return f"{r.type}|{r.from_id}|{r.to_id}"

    curated = {key(r) for r in corpus.relationships}
    extracted_keys = {key(r) for r in extracted}

    # Curated edges whose source clause text actually names the target can be recovered from text at all.
    def text_supported(r: Any) -> bool:
        source = corpus.standard(r.from_id)
        clause = next((c for c in source.clauses if c.id == r.clause_id), None) if source else None
        target = corpus.standard(r.to_id)
        return bool(clause and target and target.designation in clause.text)

    supported = [r for r in corpus.relationships if text_supported(r)]
    tp = sum(1 for e in extracted if key(e) in curated)
    curated_pairs = {f"{r.from_id}|{r.to_id}" for r in corpus.relationships}
    return {
        "extractedEdges": len(extracted),
        "curatedEdges": len(corpus.relationships),
        "textSupportedCurated": len(supported),
        "typed": asdict(prf(tp, len(extracted) - tp, sum(1 for r in supported if key(r) not in extracted_keys))),
        "untypedPairPrecision": r3(
            sum(1 for e in extracted if f"{e.from_id}|{e.to_id}" in curated_pairs) / (len(extracted) or 1)
        ),
        "recallOverAllCurated": r3(tp / (len(corpus.relationships) or 1)),
        "unmatched": [f"{e.type} {e.from_id} → {e.to_id} ({e.note})" for e in extracted if key(e) not in curated],
    }


# ---------------------------------------------------------------------------
# Phase 3 — reasoning
# ---------------------------------------------------------------------------

GROUPS = ["conflict", "gap", "dependency", "outdated", "certification"]


def group_of(f: ReasoningFinding) -> Optional[str]:
    if f.kind == "verified":
        return None
    if f.kind == "conflicting":
        return "conflict"
    if f.kind == "outdated":
        return "outdated"
    if f.kind == "certification":
        return "certification"
    return "dependency" if f.rule == "dependency_gap" else "gap"


def gold_matches(g: dict[str, Any], group: str, f: ReasoningFinding) -> bool:
    return (
        g["group"] == group
        and (not g.get("standardId") or g["standardId"] == f.standard_id)
        and (not g.get("parameter") or g["parameter"] == f.parameter)
    )


def evaluate_reasoning(corpus: Corpus, split: str, data_dir: Path = DATA) -> dict[str, Any]:
    specs = [s for s in load("reasoning.json", data_dir)["specs"] if in_split(split)(s)]
    counts = {g: {"tp": 0, "fp": 0, "fn": 0} for g in GROUPS}
    errors: list[str] = []
    latencies: list[float] = []
    for spec in specs:
        start = time.perf_counter()
        result = run_pipeline(spec["text"], corpus)
        latencies.append((time.perf_counter() - start) * 1000)
        remaining = list(spec["gold"])
        for f in result.findings:
            group = group_of(f)
            if not group:
                continue
            i = next((i for i, g in enumerate(remaining) if gold_matches(g, group, f)), -1)
            if i >= 0:
                counts[group]["tp"] += 1
                remaining.pop(i)
            else:
                counts[group]["fp"] += 1
                errors.append(f"{spec['id']}: unexpected {group} [{f.rule}] {f.title} ({f.standard_id or '—'})")
        for g in remaining:
            counts[g["group"]]["fn"] += 1
            errors.append(f"{spec['id']}: missed {g['group']} {g.get('standardId', '')} {g.get('parameter', '')}".strip())
    total = {k: sum(counts[g][k] for g in GROUPS) for k in ("tp", "fp", "fn")}
    return {
        "specs": len(specs),
        "overall": asdict(prf(total["tp"], total["fp"], total["fn"])),
        "byGroup": {g: asdict(prf(**counts[g])) for g in GROUPS},
        "meanLatencyMs": r3(mean(latencies)),
        "errors": errors,
    }


def evaluate_all(split: str = "all", corpus: Optional[Corpus] = None) -> dict[str, Any]:
    corpus = corpus or seed_corpus()
    return {
        "split": split,
        "corpusVersion": corpus.version,
        "requirements": evaluate_requirements(corpus, split),
        "retrieval": {name: evaluate_retrieval(corpus, split, opts) for name, opts in RETRIEVAL_ABLATIONS.items()},
        "resolution": evaluate_resolution(corpus, split),
        "relations": evaluate_relations(split),
        "graph": evaluate_graph_construction(corpus),
        "reasoning": evaluate_reasoning(corpus, split),
    }
