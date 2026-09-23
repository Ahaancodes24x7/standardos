"""Evaluation regression gate.

Fails if a change drops any headline metric below its floor. Floors sit a few
points under the values in eval/results/latest.md, so they catch regressions
without demanding perfection on small datasets. Raise them when the pipeline
improves.
"""

from __future__ import annotations

import pytest

from eval.evaluate import evaluate_all

FLOORS = {
    "requirement_f1": 0.9,
    "classification_accuracy": 0.72,
    "attribute_f1": 0.88,
    "standard_recall_at3": 0.95,
    "standard_mrr": 0.9,
    "clause_recall_at3": 0.9,
    "resolution_accuracy": 0.95,
    "relation_f1": 0.9,
    "graph_typed_precision": 0.7,
    "reasoning_f1": 0.9,
}


@pytest.fixture(scope="module")
def results():
    return evaluate_all("all")


def test_phase1(results):
    req = results["requirements"]
    assert req["identification"]["f1"] >= FLOORS["requirement_f1"]
    assert req["classification"]["accuracy"] >= FLOORS["classification_accuracy"]
    assert req["attributes"]["f1"] >= FLOORS["attribute_f1"]


def test_phase2(results):
    retrieval = results["retrieval"]["bm25+rerank"]
    assert retrieval["standard"]["recallAt3"] >= FLOORS["standard_recall_at3"]
    assert retrieval["standard"]["mrr"] >= FLOORS["standard_mrr"]
    assert retrieval["clause"]["recallAt3"] >= FLOORS["clause_recall_at3"]
    assert results["resolution"]["accuracy"] >= FLOORS["resolution_accuracy"]
    assert results["relations"]["typedRelation"]["f1"] >= FLOORS["relation_f1"]
    assert results["graph"]["typed"]["precision"] >= FLOORS["graph_typed_precision"]


def test_phase3(results):
    assert results["reasoning"]["overall"]["f1"] >= FLOORS["reasoning_f1"]
