"""Markdown rendering for run records, the run index and run comparisons."""

from __future__ import annotations

import json
from typing import Any

from . import datasets as dsreg
from .metrics import paired_diff_ci

RESULTS = dsreg.ROOT / "results"

DOC_COLUMNS = [
    ("id_f1", "Req. ident. F1"),
    ("id_precision", "Ident. P"),
    ("id_recall", "Ident. R"),
    ("cls_accuracy", "Class. acc."),
    ("cls_macro_f1", "Class. macro-F1"),
    ("attr_f1", "Attr. F1"),
    ("map_accuracy", "Mapping acc."),
    ("fnd_precision", "Findings P"),
    ("fnd_recall", "Findings R"),
    ("fnd_f1", "Findings F1"),
    ("latency_ms", "ms/doc"),
]
GROUP_COLUMNS = [(f"fnd_{g}_f1", g) for g in ["conflict", "gap", "dependency", "outdated", "certification"]]
RETRIEVAL_COLUMNS = [
    ("std_r1", "Std R@1"),
    ("std_r3", "Std R@3"),
    ("std_mrr", "Std MRR"),
    ("ndcg5", "nDCG@5"),
    ("cl_r1", "Clause R@1"),
    ("cl_r3", "Clause R@3"),
    ("cl_mrr", "Clause MRR"),
]
PERCENT = {"latency_ms": False, "std_mrr": False, "cl_mrr": False, "ndcg5": False}


def fmt(metric: str, value: float, ci: list[float] | None = None) -> str:
    if metric == "latency_ms":
        return f"{value:.0f}"
    if PERCENT.get(metric, True):
        text = f"{value * 100:.1f}"
        return f"{text} <sub>[{ci[0] * 100:.0f}–{ci[1] * 100:.0f}]</sub>" if ci and ci[0] != ci[1] else text
    text = f"{value:.3f}"
    return f"{text} <sub>[{ci[0]:.2f}–{ci[1]:.2f}]</sub>" if ci and ci[0] != ci[1] else text


def _has(task: dict[str, Any], prefix: str) -> bool:
    return any(k.startswith(prefix) for k in task["metrics"]) and task["n"] > 0


def render_run(record: dict[str, Any]) -> str:
    cfg = record["config"]
    lines = [
        f"# Evaluation run `{record['run_id']}`",
        "",
        f"Config **{cfg['name']}** · pipeline `{record['pipeline_version']}` · corpus `{record['corpus_version']}` · "
        f"commit `{record.get('git_commit') or 'n/a'}` · {record['created_at']} · {record['duration_s']} s",
        "",
        "Percentages with a 95% bootstrap CI (resampling documents/queries) in brackets. Split roles: "
        "**open** = used in development; **contaminated** = inspected during changes (report only); "
        "**blind** = frozen, scored only on request.",
        "",
    ]
    if record.get("label"):
        lines += [f"> {record['label']}", ""]
    tasks = record["tasks"]

    docs = [t for t in tasks if t["task"] == "documents"]
    if docs:
        lines += ["## Documents: extraction, classification, mapping, findings", ""]
        lines += ["| Dataset / split / format | Role | n | " + " | ".join(c for _, c in DOC_COLUMNS) + " |"]
        lines += ["| --- " * (len(DOC_COLUMNS) + 3) + "|"]
        for t in docs:
            cells = []
            for m, _ in DOC_COLUMNS:
                shown = (
                    (m.startswith(("id_", "cls_", "attr_")) and t.get("has_requirements"))
                    or (m == "map_accuracy" and t.get("has_mapping"))
                    or (m.startswith("fnd_") and t.get("has_findings"))
                    or m == "latency_ms"
                )
                cells.append(fmt(m, t["metrics"].get(m, 0.0), t["ci"].get(m)) if shown else "—")
            lines.append(f"| {t['dataset']} / {t['split']} / {t['variant']} | {t['role']} | {t['n']} | " + " | ".join(cells) + " |")
        lines += ["", "### Findings F1 by detector", ""]
        lines += ["| Dataset / split / format | " + " | ".join(c for _, c in GROUP_COLUMNS) + " |", "| --- " * (len(GROUP_COLUMNS) + 1) + "|"]
        for t in docs:
            if t.get("has_findings"):
                lines.append(
                    f"| {t['dataset']} / {t['split']} / {t['variant']} | "
                    + " | ".join(fmt(m, t["metrics"].get(m, 0.0)) for m, _ in GROUP_COLUMNS)
                    + " |"
                )
        lines.append("")

    ret = [t for t in tasks if t["task"] == "retrieval"]
    if ret:
        lines += ["## Retrieval (isolated requirement sentences)", ""]
        lines += ["| Dataset / split | Configuration | n | " + " | ".join(c for _, c in RETRIEVAL_COLUMNS) + " |"]
        lines += ["| --- " * (len(RETRIEVAL_COLUMNS) + 3) + "|"]
        for t in ret:
            lines.append(
                f"| {t['dataset']} / {t['split']} | {t['variant']} | {t['n']} | "
                + " | ".join(fmt(m, t["metrics"][m], t["ci"].get(m)) for m, _ in RETRIEVAL_COLUMNS)
                + " |"
            )
        lines.append("")

    other = [t for t in tasks if t["task"] in ("resolution", "relations", "graph")]
    if other:
        lines += ["## Resolution, relations, graph construction", "", "| Task | Dataset / split | n | Metrics |", "| --- | --- | --- | --- |"]
        for t in other:
            ms = ", ".join(f"{k} {fmt(k, v, t['ci'].get(k))}" for k, v in t["metrics"].items() if not k.endswith(("precision", "recall")) or t["task"] != "graph" or k.startswith("edge"))
            lines.append(f"| {t['task']} | {t['dataset']} / {t['split']} | {t['n']} | {ms} |")
        lines.append("")
    lines += ["## Configuration", "", "```json", json.dumps(cfg, indent=2), "```", ""]
    return "\n".join(lines)


def write_index() -> None:
    """Regenerate results/INDEX.md: one row per run with headline metrics on open data."""
    runs = sorted((RESULTS / "runs").glob("*/record.json"))
    lines = [
        "# Evaluation runs",
        "",
        "Generated by `python -m evaluation index`. Headline columns use **open** splits only "
        "(realworld_v2/dev TXT, component dev+test retrieval); contaminated and blind results are in each run's report.",
        "",
        "| Run | Config | Pipeline | RW2 ident. F1 | RW2 class. macro-F1 | RW2 mapping | RW2 findings F1 | T1 findings F1 | Component heldout findings F1 | Blind scored |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for path in runs:
        rec = json.loads(path.read_text(encoding="utf-8"))

        def m(task: str, ds: str, split: str, variant: str, metric: str) -> str:
            for t in rec["tasks"]:
                if (t["task"], t["dataset"], t["split"], t["variant"]) == (task, ds, split, variant):
                    v = t["metrics"].get(metric)
                    return f"{v * 100:.1f}" if v is not None else "—"
            return "—"

        lines.append(
            f"| [{rec['run_id']}](runs/{rec['run_id']}/report.md) | {rec['config']['name']} | {rec['pipeline_version']} | "
            f"{m('documents', 'realworld_v2', 'dev', 'txt', 'id_f1')} | {m('documents', 'realworld_v2', 'dev', 'txt', 'cls_macro_f1')} | "
            f"{m('documents', 'realworld_v2', 'dev', 'txt', 'map_accuracy')} | {m('documents', 'realworld_v2', 'dev', 'txt', 'fnd_f1')} | "
            f"{m('documents', 'tenders_v1', 'all', 'txt', 'fnd_f1')} | {m('documents', 'component', 'heldout', 'txt', 'fnd_f1')} | "
            f"{', '.join(rec.get('blind_scored', [])) or '—'} |"
        )
    (RESULTS / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_compare(
    rec_a: dict[str, Any], rec_b: dict[str, Any], items_a: dict[str, list], items_b: dict[str, list], aggregators: dict
) -> str:
    lines = [
        f"# Comparison: `{rec_a['run_id']}` ({rec_a['config']['name']}) → `{rec_b['run_id']}` ({rec_b['config']['name']})",
        "",
        "Δ = B − A in points; 95% paired-bootstrap CI of Δ in brackets. ▲/▼ = CI excludes zero.",
        "",
    ]
    by_key_b = {f"{t['task']}|{t['dataset']}|{t['split']}|{t['variant']}": t for t in rec_b["tasks"]}
    headline = {
        "documents": ["id_f1", "cls_accuracy", "cls_macro_f1", "attr_f1", "map_accuracy", "fnd_precision", "fnd_recall", "fnd_f1",
                      "fnd_conflict_f1", "fnd_gap_f1", "fnd_dependency_f1", "fnd_outdated_f1", "fnd_certification_f1"],
        "retrieval": ["std_r1", "std_r3", "std_mrr", "cl_r1", "cl_r3"],
        "resolution": ["res_ok", "edition_ok"],
        "relations": ["rel_f1"],
        "graph": ["edge_precision", "edge_recall", "edge_f1"],
    }
    lines += ["| Task | Dataset / split / variant | Role | Metric | A | B | Δ | CI |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    flips: list[str] = []
    for ta in rec_a["tasks"]:
        key = f"{ta['task']}|{ta['dataset']}|{ta['split']}|{ta['variant']}"
        tb = by_key_b.get(key)
        if not tb:
            continue
        ia, ib = items_a.get(key, []), items_b.get(key, [])
        pairs_ok = [x["item"] for x in ia] == [x["item"] for x in ib]
        diff = paired_diff_ci(ia, ib, aggregators[ta["task"]]) if pairs_ok else {}
        for metric in headline[ta["task"]]:
            if metric not in ta["metrics"] or metric not in tb["metrics"]:
                continue
            a, b = ta["metrics"][metric], tb["metrics"][metric]
            if metric.startswith(("fnd_",)) and ta["metrics"].get("fnd_tp") == 0 and a == 1.0 and b == 1.0:
                continue
            d = (b - a) * 100
            ci = diff.get(metric)
            mark = ""
            if ci and (ci[0] > 0 or ci[1] < 0):
                mark = " ▲" if d > 0 else " ▼"
            if abs(d) < 0.05 and not mark:
                continue
            ci_text = f"[{ci[0] * 100:+.1f}, {ci[1] * 100:+.1f}]" if ci else "—"
            lines.append(
                f"| {ta['task']} | {ta['dataset']} / {ta['split']} / {ta['variant']} | {ta['role']} | {metric} | "
                f"{a * 100:.1f} | {b * 100:.1f} | {d:+.1f}{mark} | {ci_text} |"
            )
        if pairs_ok and ta["task"] == "documents":
            for x, y in zip(ia, ib):
                for field in ("detail_matched_findings",):
                    gained = sorted(set(y.get(field, [])) - set(x.get(field, [])))
                    lost = sorted(set(x.get(field, [])) - set(y.get(field, [])))
                    flips += [f"{key} · {x['item']}: + found {g}" for g in gained]
                    flips += [f"{key} · {x['item']}: − lost {g}" for g in lost]
                for field, label in (("detail_unexpected_findings", "false positive"),):
                    removed = sorted(set(x.get(field, [])) - set(y.get(field, [])))
                    added = sorted(set(y.get(field, [])) - set(x.get(field, [])))
                    flips += [f"{key} · {x['item']}: + removed {label}: {g}" for g in removed]
                    flips += [f"{key} · {x['item']}: − new {label}: {g}" for g in added]
        if pairs_ok and ta["task"] == "retrieval":
            for x, y in zip(ia, ib):
                if x["std_r1"] != y["std_r1"]:
                    flips.append(f"{key} · {x['item']}: std R@1 {int(x['std_r1'])}→{int(y['std_r1'])} (top {y['detail_top3'][:1]})")
    lines += ["", f"## Item flips ({len(flips)})", ""]
    lines += [f"- {f}" for f in flips[:400]]
    if len(flips) > 400:
        lines.append(f"- … {len(flips) - 400} more")
    return "\n".join(lines) + "\n"
