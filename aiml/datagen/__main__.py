"""Generate the realworld_v2 dataset deterministically.

    uv run python -m datagen              (from aiml/)

Writes aiml/datasets/realworld_v2/{documents/*.txt|.pdf|.docx|.gold.json, retrieval.json, README.md}.
The dev split (12 documents) uses paraphrase variant 0 and the dev unit spellings;
the test split (18 documents) uses the other paraphrases and additional unit
spellings, and is registered as *blind*.
"""

from __future__ import annotations

import json
import random
import shutil
import sys

from evaluation.datasets import DATASETS
from evaluation.render import render_docx, render_pdf

from .compose import compose, queries

OUT = DATASETS / "realworld_v2"
PLAN = {"dev": (12, 11), "test": (18, 29)}  # documents, seed base


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "documents").mkdir(parents=True)
    summary = []
    for split, (count, base) in PLAN.items():
        rng = random.Random(base)
        clean = set(rng.sample(range(count), 2 if split == "dev" else 3))
        for i in range(count):
            doc_id = f"rw2-{split}-{i + 1:02d}"
            n_plants = 0 if i in clean else rng.randint(1, 4)
            g = compose(doc_id, split, package_index=i + (0 if split == "dev" else 3), n_plants=n_plants, seed=base * 1000 + i)
            stem = OUT / "documents" / doc_id
            stem.with_suffix(".txt").write_text(g.text, encoding="utf-8")
            header = f"{g.organization} — Tender {g.name.split('— ')[-1]}"
            stem.with_suffix(".pdf").write_bytes(
                render_pdf(g.text, header, blank_pages=1 if i % 4 == 3 else 0, wrap=rng.choice([80, 88, 95]), footer="Signature of Bidder")
            )
            stem.with_suffix(".docx").write_bytes(render_docx(g.text))
            gold = {
                "id": g.id, "split": g.split, "name": g.name, "organization": g.organization, "domain": g.domain,
                "plants": g.plants, "style": g.style, "requirements": g.requirements, "findings": g.findings,
            }
            (OUT / "documents" / f"{doc_id}.gold.json").write_text(json.dumps(gold, indent=1, ensure_ascii=False), encoding="utf-8")
            summary.append((doc_id, g.domain, len(g.requirements), len(g.findings), len(g.text.splitlines())))
    qs = queries("dev") + queries("test")
    (OUT / "retrieval.json").write_text(json.dumps({"queries": qs}, indent=1, ensure_ascii=False), encoding="utf-8")
    for row in summary:
        print(*row, sep=" | ")
    print(f"documents: {len(summary)}, requirements: {sum(r[2] for r in summary)}, findings: {sum(r[3] for r in summary)}, queries: {len(qs)}")


if __name__ == "__main__":
    main()
