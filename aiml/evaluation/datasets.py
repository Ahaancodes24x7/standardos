"""Dataset registry: manifest, integrity hashes, split roles and loaders.

``aiml/datasets/manifest.json`` lists every dataset with its splits. Each split has
a *role*:

* ``open``          — may be inspected and used while developing;
* ``contaminated``  — was inspected while making changes; reported, never a decision signal;
* ``blind``         — frozen and scored only with ``--include-blind``; every scoring is
                      appended to ``results/CONTAMINATION.md``.

``python -m evaluation verify`` recomputes file hashes, so a silent edit to a frozen
dataset fails loudly.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"
MANIFEST = DATASETS / "manifest.json"


@dataclass
class DocItem:
    id: str
    split: str
    name: str
    text: str
    domain: str = ""
    files: dict[str, Path] = field(default_factory=dict)  # native renderings: pdf / docx
    requirements: Optional[list[dict[str, Any]]] = None  # gold requirements
    findings: Optional[list[dict[str, Any]]] = None  # gold findings


@dataclass
class QueryItem:
    id: str
    split: str
    text: str
    standards: dict[str, int]
    clauses: list[str]


@dataclass
class Dataset:
    id: str
    version: str
    description: str
    splits: dict[str, dict[str, Any]]
    documents: list[DocItem] = field(default_factory=list)
    queries: list[QueryItem] = field(default_factory=list)
    resolution: list[dict[str, Any]] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    formats: list[str] = field(default_factory=lambda: ["txt"])

    def role(self, split: str) -> str:
        return self.splits.get(split, {}).get("role", "open")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def dataset_files(entry: dict[str, Any]) -> list[Path]:
    base = DATASETS / entry["path"]
    return sorted(p for p in base.rglob("*") if p.is_file() and p.suffix in {".json", ".txt", ".pdf", ".docx"})


def verify() -> list[str]:
    """Return a list of integrity problems (empty when every hashed file matches)."""
    problems: list[str] = []
    for entry in load_manifest()["datasets"]:
        recorded: dict[str, str] = entry.get("sha256", {})
        base = DATASETS / entry["path"]
        current = {str(p.relative_to(base)).replace("\\", "/"): sha256(p) for p in dataset_files(entry)}
        for name, digest in recorded.items():
            if name not in current:
                problems.append(f"{entry['id']}: {name} is missing")
            elif current[name] != digest:
                problems.append(f"{entry['id']}: {name} changed since it was frozen")
        for name in current:
            if recorded and name not in recorded:
                problems.append(f"{entry['id']}: {name} is not in the manifest")
    return problems


def freeze(dataset_id: str) -> None:
    """Record hashes for every file of a dataset (used once, when a dataset is published)."""
    manifest = load_manifest()
    for entry in manifest["datasets"]:
        if entry["id"] == dataset_id:
            base = DATASETS / entry["path"]
            entry["sha256"] = {str(p.relative_to(base)).replace("\\", "/"): sha256(p) for p in dataset_files(entry)}
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_component(entry: dict[str, Any]) -> Dataset:
    base = DATASETS / entry["path"]
    ds = Dataset(entry["id"], entry["version"], entry["description"], entry["splits"])
    for d in _read(base / "requirements.json")["documents"]:
        ds.documents.append(DocItem(d["id"], d["split"], d["id"], d["text"], requirements=d["requirements"]))
    for s in _read(base / "reasoning.json")["specs"]:
        ds.documents.append(DocItem(s["id"], s["split"], s["id"], s["text"], findings=s["gold"]))
    ds.queries = [QueryItem(q["id"], q["split"], q["text"], q["standards"], q["clauses"]) for q in _read(base / "retrieval.json")["queries"]]
    ds.resolution = _read(base / "resolution.json")["cases"]
    ds.relations = _read(base / "relations.json")["sentences"]
    return ds


def _load_documents(entry: dict[str, Any]) -> Dataset:
    """A directory of ``<id>.gold.json`` + ``<id>.txt`` (+ optional .pdf / .docx) and a ``retrieval.json``."""
    base = DATASETS / entry["path"]
    ds = Dataset(entry["id"], entry["version"], entry["description"], entry["splits"], formats=entry.get("formats", ["txt"]))
    for gold_path in sorted((base / "documents").glob("*.gold.json")):
        gold = _read(gold_path)
        stem = gold_path.name[: -len(".gold.json")]
        text = (gold_path.parent / f"{stem}.txt").read_text(encoding="utf-8")
        files = {
            fmt: gold_path.parent / f"{stem}.{fmt}" for fmt in ("pdf", "docx") if (gold_path.parent / f"{stem}.{fmt}").exists()
        }
        ds.documents.append(
            DocItem(
                id=gold["id"],
                split=gold.get("split", "all"),
                name=gold.get("name", gold["id"]),
                text=text,
                domain=gold.get("domain", ""),
                files=files,
                requirements=gold.get("requirements"),
                findings=gold.get("findings"),
            )
        )
    if (base / "retrieval.json").exists():
        ds.queries = [
            QueryItem(q["id"], q.get("split", "all"), q["text"], q["standards"], q["clauses"])
            for q in _read(base / "retrieval.json")["queries"]
        ]
    return ds


LOADERS = {"component": _load_component, "documents": _load_documents}


def load(dataset_id: str) -> Dataset:
    for entry in load_manifest()["datasets"]:
        if entry["id"] == dataset_id:
            return LOADERS[entry["loader"]](entry)
    raise KeyError(f"Unknown dataset {dataset_id!r}")


def all_ids() -> list[str]:
    return [e["id"] for e in load_manifest()["datasets"]]


def hashes(dataset_id: str) -> dict[str, str]:
    for entry in load_manifest()["datasets"]:
        if entry["id"] == dataset_id:
            return entry.get("sha256", {})
    return {}
