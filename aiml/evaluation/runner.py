"""Run evaluation suites and store append-only run records.

A run = one pipeline configuration scored on a set of datasets. It writes

    results/runs/<run_id>/record.json   metrics + 95% CIs per task/dataset/split/variant
    results/runs/<run_id>/items.jsonl   per-item results (what `compare` pairs up)
    results/runs/<run_id>/report.md     human-readable report

and regenerates results/INDEX.md. Existing runs are never modified.
"""

from __future__ import annotations

import json
import platform
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from standardos_aiml.config import PipelineConfig, preset, use_config
from standardos_aiml.standards.seed import seed_corpus
from standardos_aiml.version import PIPELINE_VERSION

from . import datasets as dsreg
from .metrics import Aggregator, bootstrap_ci
from .tasks import (
    DOC_AGGREGATOR,
    GRAPH_AGGREGATOR,
    RELATION_AGGREGATOR,
    RESOLUTION_AGGREGATOR,
    RETRIEVAL_ABLATIONS,
    RETRIEVAL_AGGREGATOR,
    evaluate_document,
    evaluate_graph,
    evaluate_query,
    evaluate_relation_sentence,
    evaluate_resolution_case,
)

RESULTS = dsreg.ROOT / "results"
RUNS = RESULTS / "runs"

AGGREGATORS: dict[str, Aggregator] = {
    "documents": DOC_AGGREGATOR,
    "retrieval": RETRIEVAL_AGGREGATOR,
    "resolution": RESOLUTION_AGGREGATOR,
    "relations": RELATION_AGGREGATOR,
    "graph": GRAPH_AGGREGATOR,
}


@dataclass
class TaskResult:
    task: str
    dataset: str
    split: str
    variant: str
    role: str
    items: list[dict[str, Any]]
    metrics: dict[str, float] = field(default_factory=dict)
    ci: dict[str, list[float]] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.task}|{self.dataset}|{self.split}|{self.variant}"

    def finalise(self) -> None:
        agg = AGGREGATORS[self.task]
        self.metrics = {k: round(v, 4) for k, v in agg(self.items).items()}
        self.ci = bootstrap_ci(self.items, agg)


def git_commit() -> Optional[str]:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=dsreg.ROOT, timeout=10
        ).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def run(
    config: PipelineConfig,
    dataset_ids: Optional[list[str]] = None,
    include_blind: bool = False,
    formats: Optional[list[str]] = None,
    label: str = "",
    progress: Callable[[str], None] = print,
) -> Path:
    corpus = seed_corpus()
    dataset_ids = dataset_ids or dsreg.all_ids()
    results: list[TaskResult] = []
    blind_scored: list[str] = []
    started = time.perf_counter()

    with use_config(config):
        for ds_id in dataset_ids:
            ds = dsreg.load(ds_id)
            for split, meta in ds.splits.items():
                role = meta.get("role", "open")
                if role == "blind" and not include_blind:
                    progress(f"  skip {ds_id}/{split} (blind; use --include-blind)")
                    continue
                if role == "blind":
                    blind_scored.append(f"{ds_id}/{split}")
                docs = [d for d in ds.documents if d.split == split]
                for fmt in formats or ds.formats:
                    if fmt not in ds.formats or not docs:
                        continue
                    progress(f"  documents  {ds_id}/{split}/{fmt} ({len(docs)} docs)")
                    results.append(
                        TaskResult("documents", ds_id, split, fmt, role, [evaluate_document(d, fmt, corpus, config) for d in docs])
                    )
                queries = [q for q in ds.queries if q.split == split]
                if queries:
                    for name, opts in RETRIEVAL_ABLATIONS.items():
                        progress(f"  retrieval  {ds_id}/{split}/{name} ({len(queries)} queries)")
                        results.append(
                            TaskResult("retrieval", ds_id, split, name, role, [evaluate_query(q, corpus, opts) for q in queries])
                        )
                cases = [c for c in ds.resolution if c["split"] == split]
                if cases:
                    results.append(TaskResult("resolution", ds_id, split, "-", role, [evaluate_resolution_case(c, corpus) for c in cases]))
                sentences = [s for s in ds.relations if s["split"] == split]
                if sentences:
                    results.append(TaskResult("relations", ds_id, split, "-", role, [evaluate_relation_sentence(s) for s in sentences]))
        results.append(TaskResult("graph", "corpus", corpus.version, "-", "open", evaluate_graph(corpus)))

    for r in results:
        r.finalise()

    created = datetime.now(timezone.utc)
    run_id = f"{created.strftime('%Y%m%d-%H%M%S')}_{config.name}"
    out = RUNS / run_id
    out.mkdir(parents=True, exist_ok=False)
    record = {
        "run_id": run_id,
        "label": label,
        "created_at": created.isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "pipeline_version": PIPELINE_VERSION,
        "corpus_version": corpus.version,
        "config": config.to_dict(),
        "include_blind": include_blind,
        "blind_scored": blind_scored,
        "datasets": {d: {"version": dsreg.load(d).version, "files_hashed": len(dsreg.hashes(d))} for d in dataset_ids},
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "duration_s": round(time.perf_counter() - started, 1),
        "tasks": [
            {
                "task": r.task, "dataset": r.dataset, "split": r.split, "variant": r.variant, "role": r.role,
                "n": len(r.items), "metrics": r.metrics, "ci": r.ci,
                "has_requirements": any("id_tp" in i for i in r.items),
                "has_findings": any("fnd_tp" in i for i in r.items),
                "has_mapping": sum(i.get("map_n", 0) for i in r.items) > 0,
            }
            for r in results
        ],
    }
    (out / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "items.jsonl").open("w", encoding="utf-8") as fh:
        for r in results:
            for item in r.items:
                fh.write(json.dumps({"key": r.key, **item}, ensure_ascii=False) + "\n")
    from .report import render_run, write_index

    (out / "report.md").write_text(render_run(record), encoding="utf-8")
    if blind_scored:
        with (RESULTS / "CONTAMINATION.md").open("a", encoding="utf-8") as fh:
            fh.write(f"| {created.isoformat(timespec='seconds')} | blind scoring | {', '.join(blind_scored)} | run `{run_id}` ({config.name}) |\n")
    write_index()
    progress(f"run {run_id} written ({record['duration_s']} s)")
    return out


def load_record(run: str) -> dict[str, Any]:
    path = RUNS / run / "record.json" if not Path(run).exists() else Path(run) / "record.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_items(run: str) -> dict[str, list[dict[str, Any]]]:
    path = (RUNS / run if not Path(run).exists() else Path(run)) / "items.jsonl"
    grouped: dict[str, list[dict[str, Any]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        grouped.setdefault(item.pop("key"), []).append(item)
    return grouped


def resolve_config(name: str) -> PipelineConfig:
    return preset(name)
