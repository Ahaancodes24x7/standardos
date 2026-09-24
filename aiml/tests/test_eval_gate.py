"""Regression gate: the default pipeline must hold its quality on the *open* splits.

Only open (development) splits are scored here — never blind ones — so running
the test suite cannot leak test data into development. Thresholds sit a little
below the v3 results recorded in results/runs; lower one only with a run record
explaining why.
"""

import pytest

from evaluation import datasets as dsreg
from evaluation.tasks import DOC_AGGREGATOR, evaluate_document
from standardos_aiml.config import preset
from standardos_aiml.standards.seed import seed_corpus

corpus = seed_corpus()


def _score(dataset: str, split: str, config: str) -> dict[str, float]:
    ds = dsreg.load(dataset)
    assert ds.role(split) == "open", "the gate may only score open splits"
    cfg = preset(config)
    items = [evaluate_document(d, "txt", corpus, cfg) for d in ds.documents if d.split == split]
    return DOC_AGGREGATOR(items)


def test_datasets_are_frozen():
    assert dsreg.verify() == []


@pytest.mark.parametrize(
    "dataset,split,floors",
    [
        ("realworld_v2", "dev", {"id_f1": 0.97, "cls_macro_f1": 0.75, "attr_f1": 0.93, "map_accuracy": 0.92, "fnd_f1": 0.90}),
        # dev2: wording no rule was written against — the generalisation floor.
        ("realworld_v2", "dev2", {"id_f1": 0.97, "attr_f1": 0.93, "fnd_precision": 0.9, "fnd_f1": 0.9}),
        ("component", "dev", {"fnd_f1": 0.88}),
    ],
)
def test_default_quality_floor(dataset, split, floors):
    m = _score(dataset, split, "v3.1")
    for metric, floor in floors.items():
        assert m[metric] >= floor, f"{dataset}/{split} {metric} = {m[metric]:.3f} < {floor}"


def test_v3_improves_on_legacy_findings():
    """Every audit fix is behind a flag; the v3 preset must beat the 2.1 behaviour it replaced."""
    assert _score("realworld_v2", "dev", "v3")["fnd_f1"] > _score("realworld_v2", "dev", "legacy-2.1")["fnd_f1"] + 0.1


def test_v31_generalises_better_than_v3():
    """v3.1 exists to close the dev→unseen-wording gap; it must not lose on dev while doing it."""
    assert _score("realworld_v2", "dev2", "v3.1")["fnd_f1"] > _score("realworld_v2", "dev2", "v3")["fnd_f1"] + 0.2
    assert _score("realworld_v2", "dev", "v3.1")["fnd_f1"] >= _score("realworld_v2", "dev", "v3")["fnd_f1"]
