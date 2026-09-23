"""StandardOS benchmark on tender-realistic specifications.

    uv run python -m benchmark.run            (from aiml/)

Scores the pipeline on six full specifications in three formats (TXT, PDF,
DOCX) and on 50 retrieval queries, and writes benchmark/results/latest.{md,json}.
Matching and metrics are the same functions the eval harness uses.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from standardos_aiml.pipeline import run_pipeline
from standardos_aiml.standards.seed import seed_corpus
from standardos_aiml.version import PIPELINE_VERSION

from eval.evaluate import (
    GROUPS,
    RETRIEVAL_ABLATIONS,
    evaluate_retrieval,
    gold_matches,
    group_of,
    prf,
    r3,
    score_attributes,
    text_matches,
)

from .render import render_docx, render_pdf

ROOT = Path(__file__).parent
DOCS = ROOT / "documents"
FORMATS = ("txt", "pdf", "docx")


def load_documents() -> list[dict[str, Any]]:
    docs = []
    for gold_path in sorted(DOCS.glob("*.gold.json")):
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        gold["text"] = gold_path.with_name(gold_path.name.replace(".gold.json", ".txt")).read_text(encoding="utf-8")
        docs.append(gold)
    return docs


def source_for(doc: dict[str, Any], fmt: str) -> Any:
    if fmt == "txt":
        return doc["text"]
    if fmt == "pdf":
        return (render_pdf(doc["text"], f"{doc['name']} — technical specification"), f"{doc['id']}.pdf")
    return (render_docx(doc["text"]), f"{doc['id']}.docx")


def score_document(doc: dict[str, Any], fmt: str, corpus) -> dict[str, Any]:
    start = time.perf_counter()
    result = run_pipeline(source_for(doc, fmt), corpus)
    latency = (time.perf_counter() - start) * 1000
    predicted = result.requirements
    used: set[str] = set()
    tp = fn = a_tp = a_fp = a_fn = 0
    confusion: list[tuple[str, str]] = []
    misses: list[str] = []
    for gold in doc["requirements"]:
        match = next((p for p in predicted if p.id not in used and text_matches(p.text, gold["text"])), None)
        if not match:
            fn += 1
            a_fn += len(gold["attributes"])
            misses.append(gold["text"])
            continue
        used.add(match.id)
        tp += 1
        confusion.append((gold["category"], match.category))
        s_tp, s_fp, s_fn = score_attributes(match, gold["attributes"])
        a_tp, a_fp, a_fn = a_tp + s_tp, a_fp + s_fp, a_fn + s_fn
    spurious = [p.text for p in predicted if p.id not in used]

    remaining = list(doc["findings"])
    counts = {g: {"tp": 0, "fp": 0, "fn": 0} for g in GROUPS}
    unexpected: list[str] = []
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
            unexpected.append(f"{group} [{f.rule}] {f.title} ({f.standard_id or '—'})")
    for g in remaining:
        counts[g["group"]]["fn"] += 1
    return {
        "id": doc["id"],
        "format": fmt,
        "latencyMs": round(latency, 1),
        "pages": len(result.document.pages),
        "parser": result.document.parser,
        "req": {"tp": tp, "fp": len(spurious), "fn": fn},
        "attr": {"tp": a_tp, "fp": a_fp, "fn": a_fn},
        "confusion": confusion,
        "findings": counts,
        "readiness": result.readiness.score,
        "predictedFindings": [
            {"kind": f.kind, "rule": f.rule, "severity": f.severity, "title": f.title, "standardId": f.standard_id}
            for f in result.findings
        ],
        "repairs": len(result.repairs),
        "misses": misses,
        "spurious": spurious,
        "unexpectedFindings": unexpected,
        "missedFindings": [f"{g['group']} {g.get('standardId', '')} {g.get('parameter', '')} — {g.get('why', '')}".strip() for g in remaining],
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def total(key: str, sub: str) -> int:
        return sum(r[key][sub] for r in rows)

    confusion = [pair for r in rows for pair in r["confusion"]]
    labels = list(dict.fromkeys(label for pair in confusion for label in pair))
    per_class = {
        label: prf(
            sum(1 for g, p in confusion if g == label and p == label),
            sum(1 for g, p in confusion if g != label and p == label),
            sum(1 for g, p in confusion if g == label and p != label),
        ).f1
        for label in labels
    }
    by_group = {
        g: asdict(prf(*(sum(r["findings"][g][k] for r in rows) for k in ("tp", "fp", "fn")))) for g in GROUPS
    }
    overall = asdict(
        prf(*(sum(r["findings"][g][k] for r in rows for g in GROUPS) for k in ("tp", "fp", "fn")))
    )
    return {
        "identification": asdict(prf(total("req", "tp"), total("req", "fp"), total("req", "fn"))),
        "classification": {
            "accuracy": r3(sum(1 for g, p in confusion if g == p) / (len(confusion) or 1)),
            "macroF1": r3(statistics.mean(per_class.values()) if per_class else 0),
            "perClassF1": per_class,
            "n": len(confusion),
        },
        "attributes": asdict(prf(total("attr", "tp"), total("attr", "fp"), total("attr", "fn"))),
        "findings": {"overall": overall, "byGroup": by_group},
        "meanLatencyMs": round(statistics.mean(r["latencyMs"] for r in rows), 1),
    }


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def main(argv: list[str]) -> None:
    corpus = seed_corpus()
    docs = load_documents()
    rows = {fmt: [score_document(d, fmt, corpus) for d in docs] for fmt in FORMATS}
    summary = {fmt: aggregate(rows[fmt]) for fmt in FORMATS}
    data_dir = ROOT
    retrieval = {
        name: evaluate_retrieval(corpus, "all", opts, data_dir=data_dir) for name, opts in RETRIEVAL_ABLATIONS.items()
    }

    n_req = sum(len(d["requirements"]) for d in docs)
    n_find = sum(len(d["findings"]) for d in docs)
    md = [
        f"# StandardOS benchmark — {PIPELINE_VERSION}",
        "",
        f"Corpus `{corpus.version}` · generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        f"{len(docs)} tender-realistic specifications ({n_req} gold requirements, {n_find} gold findings) in three "
        "formats, plus 50 retrieval queries. Gold labels were written before the system was run on these documents, "
        "and no engine code or weights were changed after scoring. See `benchmark/README.md` for how the set was "
        "built and its limits.",
        "",
        "## Headline (TXT input)",
        "",
    ]
    t = summary["txt"]
    md += [
        "| Task | Metric | Value |",
        "| --- | --- | --- |",
        f"| Requirement identification | P / R / F1 | {pct(t['identification']['precision'])} / {pct(t['identification']['recall'])} / {pct(t['identification']['f1'])} |",
        f"| Requirement classification | accuracy / macro-F1 | {pct(t['classification']['accuracy'])} / {pct(t['classification']['macroF1'])} |",
        f"| Attribute extraction | P / R / F1 | {pct(t['attributes']['precision'])} / {pct(t['attributes']['recall'])} / {pct(t['attributes']['f1'])} |",
        f"| Compliance findings | P / R / F1 | {pct(t['findings']['overall']['precision'])} / {pct(t['findings']['overall']['recall'])} / {pct(t['findings']['overall']['f1'])} |",
        f"| Standard retrieval (bm25+rerank) | R@1 / R@3 / MRR | {pct(retrieval['bm25+rerank']['standard']['recallAt1'])} / {pct(retrieval['bm25+rerank']['standard']['recallAt3'])} / {retrieval['bm25+rerank']['standard']['mrr']:.3f} |",
        f"| Clause retrieval (bm25+rerank) | R@1 / R@3 | {pct(retrieval['bm25+rerank']['clause']['recallAt1'])} / {pct(retrieval['bm25+rerank']['clause']['recallAt3'])} |",
        f"| Latency | mean per specification | {t['meanLatencyMs']} ms |",
        "",
        "## By input format",
        "",
        "| Format | Identification P / R / F1 | Classification acc. | Attribute F1 | Findings P / R / F1 | Mean latency |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for fmt in FORMATS:
        s = summary[fmt]
        i, f = s["identification"], s["findings"]["overall"]
        md.append(
            f"| {fmt.upper()} | {pct(i['precision'])} / {pct(i['recall'])} / {pct(i['f1'])} | {pct(s['classification']['accuracy'])} | "
            f"{pct(s['attributes']['f1'])} | {pct(f['precision'])} / {pct(f['recall'])} / {pct(f['f1'])} | {s['meanLatencyMs']} ms |"
        )

    md += ["", "## Compliance findings by detector (TXT)", "", "| Detector | Precision | Recall | F1 | TP/FP/FN |", "| --- | --- | --- | --- | --- |"]
    for g, m in t["findings"]["byGroup"].items():
        md.append(f"| {g} | {pct(m['precision'])} | {pct(m['recall'])} | {pct(m['f1'])} | {m['tp']}/{m['fp']}/{m['fn']} |")

    md += [
        "",
        "## Per document (TXT)",
        "",
        "| Doc | Domain | Req P / R | Findings TP/FP/FN | Readiness | Findings raised (non-verified) | Repairs |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for d, r in zip(docs, rows["txt"]):
        req = r["req"]
        p = req["tp"] / (req["tp"] + req["fp"]) if req["tp"] + req["fp"] else 1
        rc = req["tp"] / (req["tp"] + req["fn"]) if req["tp"] + req["fn"] else 1
        ft = {k: sum(r["findings"][g][k] for g in GROUPS) for k in ("tp", "fp", "fn")}
        raised = sum(1 for f in r["predictedFindings"] if f["kind"] != "verified")
        md.append(
            f"| {d['id']} | {d['domain']} | {pct(p)} / {pct(rc)} | {ft['tp']}/{ft['fp']}/{ft['fn']} | {r['readiness']} | {raised} | {r['repairs']} |"
        )

    md += [
        "",
        "## Retrieval ablation (50 queries)",
        "",
        "| Configuration | Std R@1 | Std R@3 | Std MRR | nDCG@5 | Clause R@1 | Clause R@3 | Clause MRR |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, m in retrieval.items():
        s, c = m["standard"], m["clause"]
        md.append(
            f"| {name} | {pct(s['recallAt1'])} | {pct(s['recallAt3'])} | {s['mrr']:.3f} | {s['ndcgAt5']:.3f} | "
            f"{pct(c['recallAt1'])} | {pct(c['recallAt3'])} | {c['mrr']:.3f} |"
        )

    md += ["", "## Classification F1 by category (TXT)", "", "| Category | F1 |", "| --- | --- |"]
    for label, f1 in sorted(t["classification"]["perClassF1"].items(), key=lambda kv: -kv[1]):
        md.append(f"| {label} | {pct(f1)} |")

    md += ["", "## Error listing (TXT)", ""]
    for d, r in zip(docs, rows["txt"]):
        md.append(f"### {d['id']} — {d['name']}")
        md.append("")
        for title, items in (
            ("Missed requirements", r["misses"]),
            ("Spurious requirements", r["spurious"]),
            ("Missed findings", r["missedFindings"]),
            ("Unexpected findings", r["unexpectedFindings"]),
        ):
            if items:
                md.append(f"**{title}:**")
                md.extend(f"- {x}" for x in items)
                md.append("")
        errors = [f"{g} → {p}" for g, p in r["confusion"] if g != p]
        if errors:
            md.append(f"**Classification errors (gold → predicted):** {', '.join(errors)}")
            md.append("")
    md.append("### Retrieval misses (bm25+rerank)")
    md.append("")
    md.extend(f"- {m}" for m in retrieval["bm25+rerank"]["misses"])

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "latest.json").write_text(
        json.dumps({"summary": summary, "retrieval": retrieval, "documents": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print("\n".join(md))


if __name__ == "__main__":
    main(sys.argv[1:])
