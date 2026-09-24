"""Metric aggregators over per-item results, with bootstrap confidence intervals.

Every task emits *items* (one per document, query, citation or sentence) carrying
raw counts or ranks. Metrics are computed from items by an aggregator, so the same
aggregator gives the point estimate, a percentile bootstrap CI (resampling items),
and a paired bootstrap CI for the difference between two runs.
"""

from __future__ import annotations

import math
import random
from typing import Any, Callable, Sequence

Item = dict[str, Any]
Aggregator = Callable[[Sequence[Item]], dict[str, float]]

BOOTSTRAP_SAMPLES = 1000
SEED = 20260924


def r4(x: float) -> float:
    return math.floor(x * 10000 + 0.5) / 10000


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def prf_aggregator(prefix: str) -> Aggregator:
    """Micro P/R/F1 over items holding ``{prefix}_tp``, ``_fp``, ``_fn`` counts."""

    def agg(items: Sequence[Item]) -> dict[str, float]:
        tp = sum(i.get(f"{prefix}_tp", 0) for i in items)
        fp = sum(i.get(f"{prefix}_fp", 0) for i in items)
        fn = sum(i.get(f"{prefix}_fn", 0) for i in items)
        p, r, f = prf(tp, fp, fn)
        return {f"{prefix}_precision": p, f"{prefix}_recall": r, f"{prefix}_f1": f}

    return agg


def classification_aggregator(items: Sequence[Item]) -> dict[str, float]:
    """Accuracy and macro-F1 over ``pairs`` = [[gold, predicted], …] carried by each item."""
    pairs = [tuple(p) for i in items for p in i.get("pairs", [])]
    if not pairs:
        return {"cls_accuracy": 0.0, "cls_macro_f1": 0.0}
    labels = sorted({label for pair in pairs for label in pair})
    f1s = []
    for label in labels:
        tp = sum(1 for g, p in pairs if g == label and p == label)
        fp = sum(1 for g, p in pairs if g != label and p == label)
        fn = sum(1 for g, p in pairs if g == label and p != label)
        f1s.append(prf(tp, fp, fn)[2])
    return {
        "cls_accuracy": sum(1 for g, p in pairs if g == p) / len(pairs),
        "cls_macro_f1": sum(f1s) / len(f1s),
    }


def mean_aggregator(*fields: str) -> Aggregator:
    def agg(items: Sequence[Item]) -> dict[str, float]:
        n = len(items) or 1
        return {f: sum(i.get(f, 0.0) for i in items) / n for f in fields}

    return agg


def combine(*aggs: Aggregator) -> Aggregator:
    def agg(items: Sequence[Item]) -> dict[str, float]:
        out: dict[str, float] = {}
        for a in aggs:
            out.update(a(items))
        return out

    return agg


def bootstrap_ci(items: Sequence[Item], agg: Aggregator, samples: int = BOOTSTRAP_SAMPLES) -> dict[str, list[float]]:
    """95% percentile CI per metric, resampling items with replacement."""
    if len(items) < 2:
        point = agg(items)
        return {k: [r4(v), r4(v)] for k, v in point.items()}
    rng = random.Random(SEED)
    draws: dict[str, list[float]] = {}
    n = len(items)
    for _ in range(samples):
        sample = [items[rng.randrange(n)] for _ in range(n)]
        for k, v in agg(sample).items():
            draws.setdefault(k, []).append(v)
    return {k: [r4(_pct(v, 2.5)), r4(_pct(v, 97.5))] for k, v in draws.items()}


def paired_diff_ci(
    items_a: Sequence[Item], items_b: Sequence[Item], agg: Aggregator, samples: int = BOOTSTRAP_SAMPLES
) -> dict[str, list[float]]:
    """95% CI of metric(B) − metric(A), resampling the same item indices in both runs."""
    n = len(items_a)
    if n != len(items_b) or n < 2:
        return {}
    rng = random.Random(SEED)
    draws: dict[str, list[float]] = {}
    for _ in range(samples):
        idx = [rng.randrange(n) for _ in range(n)]
        ma = agg([items_a[i] for i in idx])
        mb = agg([items_b[i] for i in idx])
        for k in ma:
            draws.setdefault(k, []).append(mb[k] - ma[k])
    return {k: [r4(_pct(v, 2.5)), r4(_pct(v, 97.5))] for k, v in draws.items()}


def _pct(values: list[float], q: float) -> float:
    ordered = sorted(values)
    k = (len(ordered) - 1) * q / 100
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return ordered[int(k)]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)
