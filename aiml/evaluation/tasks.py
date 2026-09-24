"""Evaluation tasks. Each returns a list of items (dicts) for one dataset/split/variant.

Item fields are raw counts or ranks; ``metrics.py`` aggregates them. ``detail``
fields are human-readable and are what ``compare`` uses to list flipped items.
"""

from __future__ import annotations

import math
import re
import time
from typing import Any, Optional

from standardos_aiml.config import PipelineConfig, RetrievalOptions, use_config
from standardos_aiml.nlp.entities import extract_standard_references
from standardos_aiml.nlp.requirements import structure_fragment
from standardos_aiml.pipeline import get_engine, run_pipeline
from standardos_aiml.standards.relations import extract_corpus_relationships, extract_relations
from standardos_aiml.types import Corpus, ReasoningFinding, StructuredRequirement

from .datasets import DocItem, QueryItem
from .metrics import classification_aggregator, combine, mean_aggregator, prf_aggregator

GROUPS = ["conflict", "gap", "dependency", "outdated", "certification"]

RETRIEVAL_ABLATIONS: dict[str, RetrievalOptions] = {
    "bm25": RetrievalOptions(expansion=False, document_context=False, rerank=False, min_confidence=0, top_k=10),
    "bm25+thesaurus": RetrievalOptions(expansion=True, document_context=False, rerank=False, min_confidence=0, top_k=10),
    "bm25+rerank": RetrievalOptions(expansion=False, document_context=False, rerank=True, min_confidence=0, top_k=10),
    "bm25+thesaurus+rerank": RetrievalOptions(expansion=True, document_context=False, rerank=True, min_confidence=0, top_k=10),
}

# ---------------------------------------------------------------------------
# Matching helpers (unchanged definitions from the original harness)
# ---------------------------------------------------------------------------


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def jaccard(a: str, b: str) -> float:
    A, B = set(norm(a).split()), set(norm(b).split())
    inter = len(A & B)
    return inter / ((len(A) + len(B) - inter) or 1)


def text_matches(predicted: str, gold: str) -> bool:
    return jaccard(predicted, gold) >= 0.6 or norm(gold) in norm(predicted) or norm(predicted) in norm(gold)


def score_attributes(req: StructuredRequirement, gold: list[dict[str, Any]]) -> tuple[int, int, int]:
    """Valued attributes only; precision counted over parameters that appear in gold."""
    valued = [a for a in req.attributes if a.quantity or a.text]
    tp = 0
    for g in gold:
        for a in valued:
            if a.parameter != g["parameter"]:
                continue
            if "value" in g:
                cands = [v for v in ((a.quantity.value, a.quantity.min, a.quantity.max) if a.quantity else ()) if v is not None]
                if any(abs(v - g["value"]) <= abs(g["value"]) * 0.01 + 1e-9 for v in cands):
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


# ---------------------------------------------------------------------------
# Documents: extraction, classification, attributes, mapping, reasoning
# ---------------------------------------------------------------------------

DOC_AGGREGATOR = combine(
    prf_aggregator("id"),
    prf_aggregator("attr"),
    classification_aggregator,
    prf_aggregator("fnd"),
    *[prf_aggregator(f"fnd_{g}") for g in GROUPS],
    mean_aggregator("latency_ms"),
    # Mapping accuracy only where the dataset has mapping gold (otherwise "n/a", not 0).
    lambda items: (
        {"map_accuracy": sum(i.get("map_hit", 0) for i in items) / n}
        if (n := sum(i.get("map_n", 0) for i in items))
        else {}
    ),
)


def source_for(doc: DocItem, fmt: str) -> Any:
    if fmt == "txt":
        return doc.text
    if fmt in doc.files:
        return (doc.files[fmt].read_bytes(), doc.files[fmt].name)
    from .render import render_docx, render_pdf

    if fmt == "pdf":
        return (render_pdf(doc.text, f"{doc.name} — technical specification"), f"{doc.id}.pdf")
    return (render_docx(doc.text), f"{doc.id}.docx")


def evaluate_document(doc: DocItem, fmt: str, corpus: Corpus, config: PipelineConfig) -> dict[str, Any]:
    start = time.perf_counter()
    result = run_pipeline(source_for(doc, fmt), corpus, config=config)
    item: dict[str, Any] = {"item": doc.id, "latency_ms": (time.perf_counter() - start) * 1000}

    if doc.requirements is not None:
        predicted = result.requirements
        used: set[str] = set()
        tp = fn = a_tp = a_fp = a_fn = map_hit = map_n = 0
        pairs: list[list[str]] = []
        misses: list[str] = []
        cls_errors: list[str] = []
        map_errors: list[str] = []
        mappings = {m.requirement_id: m for m in result.mappings}
        for gold in doc.requirements:
            match = next((p for p in predicted if p.id not in used and text_matches(p.text, gold["text"])), None)
            if not match:
                fn += 1
                a_fn += len(gold.get("attributes", []))
                misses.append(gold["text"][:140])
                continue
            used.add(match.id)
            tp += 1
            pairs.append([gold["category"], match.category])
            if gold["category"] != match.category:
                cls_errors.append(f"{gold['category']}→{match.category}: {gold['text'][:100]}")
            s = score_attributes(match, gold.get("attributes", []))
            a_tp, a_fp, a_fn = a_tp + s[0], a_fp + s[1], a_fn + s[2]
            if gold.get("standard"):
                map_n += 1
                m = mappings.get(match.id)
                top = m.hits[0].standard_id if m and m.hits and (m.hits[0].confidence >= 0.35 or m.basis == "explicit_reference") else None
                if top in (gold["standard"] if isinstance(gold["standard"], list) else [gold["standard"]]):
                    map_hit += 1
                else:
                    map_errors.append(f"{gold['text'][:80]} → {top} (gold {gold['standard']})")
        spurious = [p.text[:140] for p in predicted if p.id not in used]
        item.update(
            id_tp=tp, id_fp=len(spurious), id_fn=fn, attr_tp=a_tp, attr_fp=a_fp, attr_fn=a_fn, pairs=pairs,
            map_hit=map_hit, map_n=map_n,
            detail_missed_requirements=misses, detail_spurious_requirements=spurious,
            detail_classification_errors=cls_errors, detail_mapping_errors=map_errors,
        )

    if doc.findings is not None:
        remaining = list(doc.findings)
        counts = {g: [0, 0, 0] for g in GROUPS}
        matched: list[str] = []
        unexpected: list[str] = []
        predicted = [(f, group_of(f)) for f in result.findings if group_of(f)]
        # Two-pass matching: gold items that name a standard or parameter are matched first,
        # so a generic gold item ("some gap") is not consumed by a finding that belongs elsewhere.
        unmatched: list[tuple[ReasoningFinding, str]] = []
        for specific in (True, False):
            pool = predicted if specific else unmatched
            next_pool: list[tuple[ReasoningFinding, str]] = []
            for f, group in pool:
                i = next(
                    (
                        i
                        for i, g in enumerate(remaining)
                        if bool(g.get("standardId") or g.get("parameter")) == specific and gold_matches(g, group, f)
                    ),
                    -1,
                )
                if i >= 0:
                    counts[group][0] += 1
                    g = remaining.pop(i)
                    matched.append(f"{group} {g.get('standardId', '')} {g.get('parameter', '')}".strip())
                else:
                    next_pool.append((f, group))
            unmatched = next_pool
        for f, group in unmatched:
            counts[group][1] += 1
            unexpected.append(f"{group} [{f.rule}] {f.title} ({f.standard_id or '—'})")
        for g in remaining:
            counts[g["group"]][2] += 1
        for g, (tp_, fp_, fn_) in counts.items():
            item[f"fnd_{g}_tp"], item[f"fnd_{g}_fp"], item[f"fnd_{g}_fn"] = tp_, fp_, fn_
        item["fnd_tp"] = sum(c[0] for c in counts.values())
        item["fnd_fp"] = sum(c[1] for c in counts.values())
        item["fnd_fn"] = sum(c[2] for c in counts.values())
        item["detail_matched_findings"] = matched
        item["detail_unexpected_findings"] = unexpected
        item["detail_missed_findings"] = [
            f"{g['group']} {g.get('standardId', '')} {g.get('parameter', '')} {('— ' + g['why']) if g.get('why') else ''}".strip()
            for g in remaining
        ]
    return item


# ---------------------------------------------------------------------------
# Retrieval (isolated requirement sentences, no document context)
# ---------------------------------------------------------------------------

RETRIEVAL_AGGREGATOR = mean_aggregator("std_r1", "std_r3", "std_r5", "std_mrr", "ndcg5", "cl_r1", "cl_r3", "cl_mrr")


def evaluate_query(q: QueryItem, corpus: Corpus, options: RetrievalOptions) -> dict[str, Any]:
    index = get_engine(corpus).index
    fragment = structure_fragment(q.text)
    hits = index.retrieve(fragment, [], [], options)
    ranked = [h.standard_id for h in hits]
    relevant = [sid for sid, g in q.standards.items() if g >= 2]
    first = next((i for i, sid in enumerate(ranked) if sid in relevant), -1)
    dcg = sum((2 ** q.standards.get(sid, 0) - 1) / math.log2(i + 2) for i, sid in enumerate(ranked[:5]))
    ideal = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(sorted(q.standards.values(), reverse=True)[:5]))
    clauses = [h.clause_id for h in hits] if options.rerank else index.rank_clauses(q.text, options)
    fc = next((i for i, c in enumerate(clauses) if c in q.clauses), -1)
    return {
        "item": q.id,
        "std_r1": float(first == 0),
        "std_r3": float(0 <= first < 3),
        "std_r5": float(0 <= first < 5),
        "std_mrr": 1 / (first + 1) if first >= 0 else 0.0,
        "ndcg5": dcg / ideal if ideal else 0.0,
        "cl_r1": float(fc == 0),
        "cl_r3": float(0 <= fc < 3),
        "cl_mrr": 1 / (fc + 1) if fc >= 0 else 0.0,
        "detail_top3": ranked[:3],
        "detail_expected": relevant,
    }


# ---------------------------------------------------------------------------
# Resolution, relations, graph construction
# ---------------------------------------------------------------------------

RESOLUTION_AGGREGATOR = mean_aggregator("res_ok", "edition_ok")
RELATION_AGGREGATOR = prf_aggregator("rel")
GRAPH_AGGREGATOR = combine(prf_aggregator("edge"), prf_aggregator("pair"))


def evaluate_resolution_case(c: dict[str, Any], corpus: Corpus) -> dict[str, Any]:
    refs = extract_standard_references(c["text"])
    resolved = get_engine(corpus).index.resolver.resolve(refs[0]) if refs else None
    sid = resolved.standard_id if resolved else None
    edition = resolved.edition if resolved else "unknown"
    return {
        "item": c["id"],
        "res_ok": float(sid == c["expected"]),
        "edition_ok": float(edition == c["edition"]),
        "detail": f"{sid} / {edition} (gold {c['expected']} / {c['edition']})",
    }


def evaluate_relation_sentence(s: dict[str, Any]) -> dict[str, Any]:
    gold = [tuple(r) for r in s["relations"]]
    tp = fp = 0
    errors = []
    for rel in extract_relations(s["text"]):
        pair = (rel.type, rel.reference.designation)
        if pair in gold:
            tp += 1
            gold.remove(pair)
        else:
            fp += 1
            errors.append(f"predicted {pair[0]} {pair[1]}")
    return {"item": s["id"], "rel_tp": tp, "rel_fp": fp, "rel_fn": len(gold), "detail": errors}


def evaluate_graph(corpus: Corpus) -> list[dict[str, Any]]:
    """Per source standard: extracted edges vs curated edges whose clause text names the target."""
    index = get_engine(corpus).index
    extracted = extract_corpus_relationships(corpus, index.resolver)

    def key(r: Any) -> tuple[str, str, str]:
        return (r.type, r.from_id, r.to_id)

    def supported(r: Any) -> bool:
        src = corpus.standard(r.from_id)
        clause = next((c for c in src.clauses if c.id == r.clause_id), None) if src else None
        tgt = corpus.standard(r.to_id)
        return bool(clause and tgt and tgt.designation in clause.text)

    curated_keys = {key(r) for r in corpus.relationships}
    curated_pairs = {(r.from_id, r.to_id) for r in corpus.relationships}
    ext_keys = {key(e) for e in extracted}
    items = []
    for std in corpus.standards:
        ext = [e for e in extracted if e.from_id == std.id]
        cur = [r for r in corpus.relationships if r.from_id == std.id and supported(r)]
        if not ext and not cur:
            continue
        tp = sum(1 for e in ext if key(e) in curated_keys)
        items.append(
            {
                "item": std.id,
                "edge_tp": tp,
                "edge_fp": len(ext) - tp,
                "edge_fn": sum(1 for r in cur if key(r) not in ext_keys),
                "pair_tp": sum(1 for e in ext if (e.from_id, e.to_id) in curated_pairs),
                "pair_fp": sum(1 for e in ext if (e.from_id, e.to_id) not in curated_pairs),
                "pair_fn": 0,
                "detail": [f"{e.type} → {e.to_id} ({e.note})" for e in ext if key(e) not in curated_keys],
            }
        )
    return items


def with_config(config: PipelineConfig):
    return use_config(config)
