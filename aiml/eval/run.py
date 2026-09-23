"""``python -m eval.run [dev|test|heldout|all] [--verbose]`` (run from ``aiml/``).

Prints a metrics report and writes ``eval/results/latest.json`` and ``eval/results/latest.md``.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from standardos_aiml.version import PIPELINE_VERSION

from .evaluate import evaluate_all


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def prf_row(name: str, m: dict) -> str:
    return f"| {name} | {pct(m['precision'])} | {pct(m['recall'])} | {pct(m['f1'])} | {m['tp']}/{m['fp']}/{m['fn']} |"


def main(argv: list[str]) -> None:
    split = next((a for a in argv if a in ("dev", "test", "heldout", "all")), "all")
    verbose = "--verbose" in argv
    results = {s: evaluate_all(s) for s in ("dev", "test", "heldout", "all")}
    r = results[split]

    md: list[str] = [
        f"# StandardOS evaluation — {PIPELINE_VERSION}",
        "",
        f"Corpus `{r['corpusVersion']}` · generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "Splits: **dev** was used while developing rules and weights. **test** was held out for the first run, but "
        "some fixes were then made after inspecting its errors, so it is partly contaminated (see eval/README.md). "
        "**heldout** was written after all tuning and scored once without further changes; treat it as the "
        "uncontaminated estimate, keeping in mind it is small. For a larger, tender-realistic benchmark see "
        "`aiml/benchmark/results/latest.md`.",
        "",
        "## Phase 1 — requirement extraction",
        "",
        "| Split | Identification P / R / F1 | Classification acc. / macro-F1 | Attribute P / R / F1 |",
        "| --- | --- | --- | --- |",
    ]
    for s in ("dev", "test", "heldout", "all"):
        q = results[s]["requirements"]
        i, c, a = q["identification"], q["classification"], q["attributes"]
        md.append(
            f"| {s} ({q['documents']} docs) | {pct(i['precision'])} / {pct(i['recall'])} / {pct(i['f1'])} | "
            f"{pct(c['accuracy'])} / {pct(c['macroF1'])} | {pct(a['precision'])} / {pct(a['recall'])} / {pct(a['f1'])} |"
        )

    md += [
        "",
        "## Phase 2 — standard and clause retrieval (ablation)",
        "",
        "| Split | Configuration | Std R@1 | Std R@3 | Std MRR | nDCG@5 | Clause R@1 | Clause R@3 | Clause MRR |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in ("dev", "test", "heldout"):
        for name, m in results[s]["retrieval"].items():
            st, cl = m["standard"], m["clause"]
            md.append(
                f"| {s} ({m['queries']}) | {name} | {pct(st['recallAt1'])} | {pct(st['recallAt3'])} | {st['mrr']:.3f} | "
                f"{st['ndcgAt5']:.3f} | {pct(cl['recallAt1'])} | {pct(cl['recallAt3'])} | {cl['mrr']:.3f} |"
            )

    md += [
        "",
        "## Phase 2 — entity resolution, relationship extraction, graph construction",
        "",
        "| Split | Resolution accuracy | Edition accuracy | Relation P / R / F1 |",
        "| --- | --- | --- | --- |",
    ]
    for s in ("dev", "test", "heldout", "all"):
        x = results[s]
        rel = x["relations"]["typedRelation"]
        md.append(
            f"| {s} | {pct(x['resolution']['accuracy'])} ({x['resolution']['cases']}) | "
            f"{pct(x['resolution']['editionAccuracy'])} | {pct(rel['precision'])} / {pct(rel['recall'])} / "
            f"{pct(rel['f1'])} ({x['relations']['sentences']} sentences) |"
        )
    g = r["graph"]
    md += [
        "",
        f"Graph construction from clause text: {g['extractedEdges']} edges extracted; {g['textSupportedCurated']} of "
        f"{g['curatedEdges']} curated edges are stated in clause text.",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Typed-edge precision | {pct(g['typed']['precision'])} |",
        f"| Typed-edge recall (text-supported curated edges) | {pct(g['typed']['recall'])} |",
        f"| Untyped pair precision | {pct(g['untypedPairPrecision'])} |",
        f"| Recall over all curated edges | {pct(g['recallOverAllCurated'])} |",
        "",
        "## Phase 3 — compliance reasoning",
        "",
        "| Split | Detector | Precision | Recall | F1 | TP/FP/FN |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for s in ("dev", "test", "heldout"):
        x = results[s]["reasoning"]
        md.append(prf_row(f"overall ({x['specs']} specs)", x["overall"]).replace("| ", f"| {s} | ", 1))
        for group, m in x["byGroup"].items():
            md.append(prf_row(group, m).replace("| ", f"| {s} | ", 1))
    md += [
        "",
        f"Mean end-to-end pipeline latency per specification: {r['reasoning']['meanLatencyMs']:.1f} ms "
        "(in-process, seed corpus, CPython).",
    ]

    if verbose:
        md += ["", "## Error listing", ""]

        def block(title: str, lines: list) -> None:
            if lines:
                md.extend([f"### {title}", "", *[f"- {line}" for line in lines], ""])

        block("Retrieval misses (default configuration: bm25+rerank)", r["retrieval"]["bm25+rerank"]["misses"])
        block("Resolution errors", r["resolution"]["errors"])
        block("Relation errors", r["relations"]["errors"])
        block("Extracted edges not in curated graph", r["graph"]["unmatched"])
        block("Reasoning errors", r["reasoning"]["errors"])
        block(
            "Classification errors (gold → predicted)",
            [f"{a} → {b}" for a, b in r["requirements"]["classification"]["errors"]],
        )

    out = Path(__file__).parent / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print("\n".join(md))


if __name__ == "__main__":
    main(sys.argv[1:])
