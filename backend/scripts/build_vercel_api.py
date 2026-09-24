"""Build the self-contained Vercel bundle of the API in deploy/vercel-api/.

    uv run python -m scripts.build_vercel_api        (from backend/)

A Git-connected Vercel project only sees its Root Directory, and Vercel's Python
builder installs from requirements.txt, so the API cannot import the engine from
../aiml or resolve the uv workspace. This copies what the function needs next to
its entry point:

    deploy/vercel-api/app/               ← backend/app
    deploy/vercel-api/standardos_aiml/   ← aiml/standardos_aiml
    deploy/vercel-api/results/           ← latest evaluation record per preset (Evaluation page)

Run it after changing backend/app or aiml/standardos_aiml and commit the result;
backend/tests/test_vercel_bundle.py fails while the copy is out of date.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "deploy" / "vercel-api"
SOURCES = {
    "app": ROOT / "backend" / "app",
    "standardos_aiml": ROOT / "aiml" / "standardos_aiml",
}
RESULTS = ROOT / "aiml" / "results"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def tree_digest(path: Path) -> str:
    """Content hash of a source tree (paths and bytes; caches ignored)."""
    h = hashlib.sha256()
    for f in sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"}):
        h.update(f.relative_to(path).as_posix().encode())
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def _latest_records() -> dict[str, Path]:
    """Newest run record per preset, plus the newest classifier comparison."""
    latest: dict[str, Path] = {}
    for record in sorted((RESULTS / "runs").glob("*/record.json")):
        config = json.loads(record.read_text(encoding="utf-8"))["config"]["name"]
        latest[f"runs/{config}"] = record  # sorted by run id (timestamp) → last wins
    classifiers = sorted((RESULTS / "classifiers").glob("*/record.json"))
    if classifiers:
        latest["classifiers"] = classifiers[-1]
    return latest


def build() -> dict[str, str]:
    for name, source in SOURCES.items():
        target = BUNDLE / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, ignore=IGNORE)
    results = BUNDLE / "results"
    if results.exists():
        shutil.rmtree(results)
    for key, record in _latest_records().items():
        dest = results / record.relative_to(RESULTS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(record, dest)
    digests = {name: tree_digest(source) for name, source in SOURCES.items()}
    (BUNDLE / "SOURCES.json").write_text(json.dumps(digests, indent=2) + "\n", encoding="utf-8")
    return digests


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    for name, digest in build().items():
        print(f"{name}: {digest[:12]}")
    print(f"bundle written to {BUNDLE}")
