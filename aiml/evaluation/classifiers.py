"""Train and compare requirement classifiers: lexicon vs learned models.

    uv run python -m evaluation.classifiers [--include-blind]      (from aiml/)

Training data: gold requirements of the *open* splits only (realworld_v2/dev,
component/dev), de-duplicated by text. 20% of the unique texts are held out for
model selection (early stopping, gating threshold). Test sets are wording the
models never saw:

* realworld_v2/test — other paraphrases of the same clause families (blind; logged)
* tenders_v1        — six independently written tenders (contaminated for the engine, unseen by the models)
* component/test    — the original short-document set
* component/heldout — (blind; logged)

Writes models to aiml/models/requirement-classifier/ and a report to
results/classifiers/<run_id>/.
"""

from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from standardos_aiml.ml.features import CATEGORIES, lexicon_scores, struct_vector, structure
from standardos_aiml.ml.models import ENCODER, embed, predict_hybrid, train_hybrid

from . import datasets as dsreg
from .metrics import bootstrap_ci, classification_aggregator

MODELS = dsreg.ROOT / "models" / "requirement-classifier"
OUT = dsreg.ROOT / "results" / "classifiers"


def gold_requirements(dataset: str, split: str) -> list[dict[str, Any]]:
    ds = dsreg.load(dataset)
    return [r for d in ds.documents if d.split == split and d.requirements for r in d.requirements]


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for r in rows:
        seen.setdefault(" ".join(r["text"].lower().split()), r)
    return list(seen.values())


def featurise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    texts = [r["text"] for r in rows]
    structured = [structure(t) for t in texts]
    return {
        "texts": texts,
        "y": np.array([CATEGORIES.index(r["category"]) for r in rows]),
        "struct": np.array([struct_vector(s) for s in structured], dtype=np.float32),
        "emb": embed(texts).astype(np.float32),
        "lexicon": [lexicon_scores(s) for s in structured],
    }


def score(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    items = [{"pairs": [list(p)]} for p in pairs]
    point = classification_aggregator(items)
    ci = bootstrap_ci(items, classification_aggregator)
    labels = sorted({g for g, _ in pairs})
    per_class = {}
    for label in labels:
        tp = sum(1 for g, p in pairs if g == label and p == label)
        fp = sum(1 for g, p in pairs if g != label and p == label)
        fn = sum(1 for g, p in pairs if g == label and p != label)
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        per_class[label] = round(2 * pr * rc / (pr + rc), 3) if pr + rc else 0.0
    return {"n": len(pairs), **{k: round(v, 4) for k, v in point.items()}, "ci": ci, "per_class_f1": per_class}


def main(argv: list[str]) -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    include_blind = "--include-blind" in argv
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, make_pipeline
    import joblib
    import torch

    train_rows = dedupe(gold_requirements("realworld_v2", "dev") + gold_requirements("component", "dev"))
    rng = random.Random(20260924)
    rng.shuffle(train_rows)
    n_val = max(12, len(train_rows) // 5)
    val_rows, fit_rows = train_rows[:n_val], train_rows[n_val:]
    print(f"training texts: {len(fit_rows)} fit + {len(val_rows)} validation (unique)")
    fit, val = featurise(fit_rows), featurise(val_rows)

    # --- classical baselines ------------------------------------------------------
    tfidf = make_pipeline(
        FeatureUnion([
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, lowercase=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, lowercase=True)),
        ]),
        LogisticRegression(max_iter=3000, C=8.0, class_weight="balanced"),
    )
    tfidf.fit(fit["texts"], fit["y"])
    embed_lr = LogisticRegression(max_iter=3000, C=4.0, class_weight="balanced").fit(fit["emb"], fit["y"])

    # --- hybrid neural network -----------------------------------------------------
    started = time.perf_counter()
    hybrid, train_info = train_hybrid(fit["emb"], fit["struct"], fit["y"], val["emb"], val["struct"], val["y"])
    train_info["train_seconds"] = round(time.perf_counter() - started, 1)

    # --- gating threshold on validation ------------------------------------------
    val_probs = predict_hybrid(hybrid, val["emb"], val["struct"])
    best_tau, best_f1 = 1.01, -1.0
    for tau in [0.5 + 0.025 * i for i in range(21)]:
        preds = [lex[1] if lex[2] >= tau else CATEGORIES[int(p.argmax())] for lex, p in zip(val["lexicon"], val_probs)]
        f1 = classification_aggregator([{"pairs": [[CATEGORIES[g], p]]} for g, p in zip(val["y"], preds)])["cls_macro_f1"]
        if f1 > best_f1:
            best_tau, best_f1 = tau, f1
    print(f"hybrid-nn: {train_info}; gated tau={best_tau:.3f} (validation macro-F1 {best_f1:.3f})")

    # --- save models --------------------------------------------------------------
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(tfidf, MODELS / "tfidf-lr.joblib")
    joblib.dump(embed_lr, MODELS / "embed-lr.joblib")
    torch.save(hybrid.state_dict(), MODELS / "hybrid-nn.pt")
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "encoder": ENCODER,
        "categories": CATEGORIES,
        "gate_tau": best_tau,
        "training": {"datasets": ["realworld_v2/dev", "component/dev"], "fit": len(fit_rows), "validation": len(val_rows)},
        "hybrid": train_info,
    }
    (MODELS / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # --- evaluate on unseen wording ---------------------------------------------------
    test_sets = [("tenders_v1", "all"), ("component", "test")]
    if include_blind:
        test_sets = [("realworld_v2", "test"), *test_sets, ("component", "heldout")]
    results: dict[str, dict[str, Any]] = {}
    for ds_id, split in test_sets:
        rows = gold_requirements(ds_id, split)
        feats = featurise(rows)
        gold = [CATEGORIES[i] for i in feats["y"]]
        timings: dict[str, float] = {}
        preds: dict[str, list[str]] = {}
        t = time.perf_counter(); preds["lexicon-v2"] = [lex[1] for lex in feats["lexicon"]]; timings["lexicon-v2"] = time.perf_counter() - t
        t = time.perf_counter(); preds["tfidf-lr"] = [CATEGORIES[i] for i in tfidf.predict(feats["texts"])]; timings["tfidf-lr"] = time.perf_counter() - t
        t = time.perf_counter(); preds["embed-lr"] = [CATEGORIES[i] for i in embed_lr.predict(feats["emb"])]; timings["embed-lr"] = time.perf_counter() - t
        t = time.perf_counter(); probs = predict_hybrid(hybrid, feats["emb"], feats["struct"]); timings["hybrid-nn"] = time.perf_counter() - t
        preds["hybrid-nn"] = [CATEGORIES[int(p.argmax())] for p in probs]
        preds["gated"] = [lex[1] if lex[2] >= best_tau else h for lex, h in zip(feats["lexicon"], preds["hybrid-nn"])]
        results[f"{ds_id}/{split}"] = {name: score(list(zip(gold, p))) for name, p in preds.items()}
        print(f"{ds_id}/{split} (n={len(rows)}): " + ", ".join(f"{k} {v['cls_accuracy']:.3f}/{v['cls_macro_f1']:.3f}" for k, v in results[f'{ds_id}/{split}'].items()))

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out = OUT / run_id
    out.mkdir(parents=True, exist_ok=True)
    record = {"run_id": run_id, "meta": meta, "include_blind": include_blind, "results": results}
    (out / "record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render(record), encoding="utf-8")
    if include_blind:
        with (dsreg.ROOT / "results" / "CONTAMINATION.md").open("a", encoding="utf-8") as fh:
            fh.write(f"| {meta['created_at']} | blind scoring (classifier comparison) | realworld_v2/test, component/heldout | results/classifiers/{run_id} |\n")
    print(f"report: {out / 'report.md'}")


def render(record: dict[str, Any]) -> str:
    meta = record["meta"]
    models = ["lexicon-v2", "tfidf-lr", "embed-lr", "hybrid-nn", "gated"]
    lines = [
        f"# Requirement classifier comparison `{record['run_id']}`",
        "",
        f"Trained on {meta['training']['fit']} unique requirement texts from open splits ({', '.join(meta['training']['datasets'])}); "
        f"{meta['training']['validation']} held out for early stopping and the gate threshold (τ = {meta['gate_tau']:.3f}). "
        f"Encoder `{meta['encoder']}` (frozen). Hybrid network: {meta['hybrid']}.",
        "",
        "Accuracy / macro-F1 in %, 95% bootstrap CI of macro-F1 in brackets.",
        "",
        "| Test set | n | " + " | ".join(models) + " |",
        "| --- | --- | " + " | ".join("---" for _ in models) + " |",
    ]
    for name, res in record["results"].items():
        cells = []
        for m in models:
            r = res[m]
            ci = r["ci"]["cls_macro_f1"]
            cells.append(f"{r['cls_accuracy'] * 100:.1f} / **{r['cls_macro_f1'] * 100:.1f}** <sub>[{ci[0] * 100:.0f}–{ci[1] * 100:.0f}]</sub>")
        lines.append(f"| {name} | {res['lexicon-v2']['n']} | " + " | ".join(cells) + " |")
    lines += ["", "## Per-class F1", ""]
    for name, res in record["results"].items():
        labels = sorted(res["lexicon-v2"]["per_class_f1"])
        lines += [f"### {name}", "", "| Class | " + " | ".join(models) + " |", "| --- | " + " | ".join("---" for _ in models) + " |"]
        for label in labels:
            lines.append(f"| {label} | " + " | ".join(f"{res[m]['per_class_f1'].get(label, 0) * 100:.0f}" for m in models) + " |")
        lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main(sys.argv[1:])
