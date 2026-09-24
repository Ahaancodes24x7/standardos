"""StandardOS evaluation CLI (run from ``aiml/``).

    uv run python -m evaluation run --config v3 [--datasets realworld_v2,tenders_v1] [--formats txt] [--include-blind]
    uv run python -m evaluation compare <run_a> <run_b>          # writes results/comparisons/<a>__vs__<b>.md
    uv run python -m evaluation index                            # regenerate results/INDEX.md
    uv run python -m evaluation verify                           # dataset integrity (frozen hashes)
    uv run python -m evaluation freeze <dataset>                 # record hashes when publishing a dataset
    uv run python -m evaluation presets                          # list pipeline presets
"""

from __future__ import annotations

import argparse
import sys

from standardos_aiml.config import PRESETS

from . import datasets as dsreg
from .report import render_compare, write_index
from .runner import AGGREGATORS, RESULTS, load_items, load_record, resolve_config, run


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    parser = argparse.ArgumentParser(prog="python -m evaluation")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--config", default="v3")
    p_run.add_argument("--datasets", default="")
    p_run.add_argument("--formats", default="")
    p_run.add_argument("--include-blind", action="store_true")
    p_run.add_argument("--label", default="")
    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("run_a")
    p_cmp.add_argument("run_b")
    sub.add_parser("index")
    sub.add_parser("verify")
    p_freeze = sub.add_parser("freeze")
    p_freeze.add_argument("dataset")
    sub.add_parser("presets")
    args = parser.parse_args(argv)

    if args.cmd == "verify":
        problems = dsreg.verify()
        for p in problems:
            print("FAIL", p)
        print("datasets verified" if not problems else f"{len(problems)} integrity problem(s)")
        return 1 if problems else 0
    if args.cmd == "freeze":
        dsreg.freeze(args.dataset)
        print(f"hashes recorded for {args.dataset}")
        return 0
    if args.cmd == "presets":
        for name, cfg in PRESETS.items():
            print(name, {k: v for k, v in cfg.to_dict().items() if k not in ("name", "retrieval")})
        return 0
    if args.cmd == "index":
        write_index()
        return 0
    if args.cmd == "run":
        problems = dsreg.verify()
        if problems:
            print("Refusing to run: dataset integrity problems:\n  " + "\n  ".join(problems))
            return 1
        out = run(
            resolve_config(args.config),
            [d for d in args.datasets.split(",") if d] or None,
            include_blind=args.include_blind,
            formats=[f for f in args.formats.split(",") if f] or None,
            label=args.label,
        )
        print(f"report: {out / 'report.md'}")
        return 0
    if args.cmd == "compare":
        rec_a, rec_b = load_record(args.run_a), load_record(args.run_b)
        text = render_compare(rec_a, rec_b, load_items(args.run_a), load_items(args.run_b), AGGREGATORS)
        out = RESULTS / "comparisons" / f"{rec_a['run_id']}__vs__{rec_b['run_id']}.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(text)
        print(f"written: {out}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
