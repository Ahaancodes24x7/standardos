"""The Vercel bundle (deploy/vercel-api) must contain the current API and engine code."""

import json

from scripts.build_vercel_api import BUNDLE, SOURCES, tree_digest


def test_bundle_matches_sources():
    recorded = json.loads((BUNDLE / "SOURCES.json").read_text(encoding="utf-8"))
    for name, source in SOURCES.items():
        assert recorded[name] == tree_digest(source), (
            f"deploy/vercel-api/{name} is out of date: run `uv run python -m scripts.build_vercel_api` in backend/"
        )
        assert tree_digest(BUNDLE / name) == tree_digest(source), f"deploy/vercel-api/{name} was edited by hand"


def test_bundle_entry_point_imports_the_app():
    source = (BUNDLE / "api" / "index.py").read_text(encoding="utf-8")
    assert "from app.main import app" in source
    assert (BUNDLE / "requirements.txt").read_text(encoding="utf-8").count("fastapi") == 1
