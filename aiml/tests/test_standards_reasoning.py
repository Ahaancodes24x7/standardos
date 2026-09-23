from __future__ import annotations

import re

import pytest

from standardos_aiml.nlp.entities import extract_standard_references
from standardos_aiml.nlp.requirements import structure_fragment
from standardos_aiml.pipeline import compute_readiness, get_engine, run_pipeline
from standardos_aiml.provenance import provenance
from standardos_aiml.reasoning.conflicts import compare
from standardos_aiml.reasoning.repair_validate import validate_rewrite
from standardos_aiml.samples import SAMPLE_DOCUMENTS
from standardos_aiml.standards.graph import StandardsGraph
from standardos_aiml.standards.relations import extract_relations
from standardos_aiml.standards.seed import seed_corpus
from standardos_aiml.types import ClauseConstraint, Quantity, ReasoningFinding, RequirementMapping, RetrievalHit, TextSpan

corpus = seed_corpus()
index = get_engine(corpus).index


def resolve(text: str):
    refs = extract_standard_references(text)
    return index.resolver.resolve(refs[0]) if refs else None


def sample(sample_id: str) -> str:
    return next(s.text for s in SAMPLE_DOCUMENTS if s.id == sample_id)


# ---------------------------------------------------------------------------
# Corpus, resolution, retrieval, relations, graph
# ---------------------------------------------------------------------------


def test_corpus_integrity():
    ids = {s.id for s in corpus.standards}
    clause_ids = {c.id for s in corpus.standards for c in s.clauses}
    for r in corpus.relationships:
        assert r.from_id in ids and r.to_id in ids
        assert not r.clause_id or r.clause_id in clause_ids
    assert all(e.standard_id in ids for e in corpus.events)
    assert all(item.clause_id in clause_ids for s in corpus.standards for item in s.checklist)
    assert all(s.source.kind == "curated-seed" and s.source.verified is False for s in corpus.standards)
    assert re.fullmatch(r"seed-[0-9a-f]{8}", corpus.version)


def test_corpus_version_matches_typescript_engine():
    # FNV-1a over the JSON payload, identical to the retired TypeScript implementation.
    assert corpus.version == "seed-6ada30cf"


def test_resolves_citation_variants():
    for text in ["IS 1554 (Part 1):1988", "IS 1554 (Pt. 1)", "IS 1554-1", "IS 1554"]:
        assert resolve(text).standard_id == "is-1554-1-1988"
    assert resolve("IEC 61439-1").standard_id == "is-iec-61439-1-2020"
    assert resolve("IS 3025 (Part 11)").standard_id == "is-3025"


def test_edition_classification():
    r = resolve("IS 3043:1987")
    assert (r.edition, r.replaced_by_id) == ("older", "is-3043-2018")
    assert resolve("IS 3043:2018").edition == "current"
    assert resolve("IS 694:2020").edition == "newer"
    r = resolve("IS 2190")
    assert (r.standard_id, r.edition) == (None, "unknown")
    assert resolve("IS 732:2019").provenance.confidence == 0.98
    assert resolve("IEC 60529").provenance.confidence >= 0.9
    assert resolve("IS 3025 (Part 11)").provenance.confidence < 0.9


def top(text: str):
    return index.retrieve(structure_fragment(text), [], [])[0]


def test_retrieval_without_citations():
    hit = top("Panels shall operate at an ambient air temperature of 45 °C.")
    assert (hit.standard_id, hit.clause_id) == ("is-iec-61439-1-2020", "is-iec-61439-1-2020#service-conditions")
    assert top("Nominal cover to reinforcement shall be 50 mm for very severe exposure.").standard_id == "is-456-2000"
    assert top("Total dissolved solids shall not exceed 500 mg/l.").clause_id == "is-10500-2012#tds"
    hit = top("PVC insulated armoured aluminium cables, 1.1 kV grade.")
    assert len(hit.explanation) > 10 and hit.provenance.component == "standards.rerank"
    assert 0 < hit.confidence <= 1


def test_explicit_citations_rank_first():
    fragment = structure_fragment("Cables shall conform to IS 7098 (Part 1).")
    refs = [index.resolver.resolve(r) for r in fragment.references]
    assert index.retrieve(fragment, refs, [])[0].standard_id == "is-7098-1-1988"


def test_relation_types():
    rels = extract_relations(
        "Transformers conforming to IS 1180 (Part 1) shall be type tested as per IS 2026 (Part 1). See also IS 732."
    )
    assert [(r.type, r.reference.designation) for r in rels] == [
        ("REQUIRES", "IS 1180 (Part 1)"),
        ("TESTED_BY", "IS 2026 (Part 1)"),
        ("RELATED_TO", "IS 732"),
    ]
    assert [r.type for r in extract_relations("IS 269:2015 replaces IS 8112 and IS 12269.")] == [
        "REFERENCES",
        "SUPERSEDES",
        "SUPERSEDES",
    ]


def test_graph_traversal():
    graph = StandardsGraph(corpus)
    assert graph.latest_replacement("is-8623-1-1993").id == "is-iec-61439-1-2020"
    assert graph.latest_replacement("is-3043-2018") is None
    deps = {d.id for d in graph.dependencies("is-456-2000", 2)}
    assert {"is-383-2016", "is-1786-2008", "is-269-2015", "is-516-1959"} <= deps


# ---------------------------------------------------------------------------
# Reasoning
# ---------------------------------------------------------------------------


def qty(lo, hi) -> Quantity:
    return Quantity("", TextSpan(0, 0), lo if lo is not None else hi, lo, hi, "x", "x", "eq", None)


def con(lo, hi) -> ClauseConstraint:
    return ClauseConstraint("p", "x", "x", lo, hi, "")


def test_interval_checks():
    assert compare(qty(30, 30), con(20, 40))[0] == "none"
    assert compare(qty(120, 120), con(-5, 40)) == ("disjoint", "above")
    assert compare(qty(35, 45), con(-5, 40)) == ("partial", "above")
    assert compare(qty(20, None), con(30, None)) == ("partial", "below")
    # An open end of a requirement is unstated, not infinite.
    assert compare(qty(None, 30), con(-5, 40))[0] == "none"


def test_sample_panel():
    r = run_pipeline(sample("sample-electrical-panel"), corpus)
    rules = {f"{f.rule}:{f.standard_id}" for f in r.findings}
    assert {
        "constraint_conflict:is-iec-61439-1-2020",
        "superseded_reference:is-iec-61439-1-2020",
        "superseded_reference:is-iec-60898-1-2002",
    } <= rules
    assert any(f.rule == "checklist_gap" and f.parameter == "ip_rating" for f in r.findings)
    repair = next(p for p in r.repairs if "40 °C" in p.recommended)
    assert "IS/IEC 61439-1:2020" in repair.recommended


def test_sample_pump():
    r = run_pipeline(sample("sample-water-pump"), corpus)
    conflict = next(f for f in r.findings if f.rule == "constraint_conflict")
    assert (conflict.parameter, conflict.standard_id, conflict.severity) == ("voltage_variation", "is-325-1996", "high")
    assert any(f.rule == "superseded_edition" and f.standard_id == "is-3043-2018" for f in r.findings)
    assert any(f.parameter == "pump_head" and f.kind == "missing" for f in r.findings)
    assert (
        "The motor shall be suitable for 415 V ±10 %, 50 Hz supply, in accordance with IS 325:1996."
        in [p.recommended for p in r.repairs]
    )


def test_sample_reservoir():
    r = run_pipeline(sample("sample-water-tank"), corpus)

    def conflict(p):
        return next((f for f in r.findings if f.parameter == p and f.kind == "conflicting"), None)

    assert conflict("concrete_grade").severity == "high"  # M20 < M30 for severe exposure
    assert conflict("nominal_cover") and conflict("tds")
    assert any(f.kind == "verified" and f.rule == "constraint_satisfied" for f in r.findings)
    assert any(f.rule == "superseded_reference" and f.standard_id == "is-269-2015" for f in r.findings)


def test_clean_specification_raises_no_problems():
    r = run_pipeline(
        "1. Three phase induction motors shall conform to IS 325.\n2. Rated output: 30 kW.\n"
        "3. Motors shall operate on 415 V ± 10 % and 50 Hz ± 5 % supply.\n4. Efficiency class IE3 as per IS 12615.\n"
        "5. Degree of protection: IP55.\n6. Routine tests as per IS 4029 with test certificates.\n"
        "7. Motors shall bear the ISI mark.",
        corpus,
    )
    assert [f for f in r.findings if f.kind != "verified"] == []


@pytest.mark.parametrize("sample_doc", SAMPLE_DOCUMENTS, ids=lambda s: s.id)
def test_every_finding_and_repair_is_traceable(sample_doc):
    r = run_pipeline(sample_doc.text, corpus)
    for f in r.findings:
        assert f.evidence and f.provenance.component.startswith("reasoning.")
        assert f.provenance.signals and f.provenance.confidence > 0
        for e in f.evidence:
            if e.kind == "requirement_text" and e.span:
                assert r.document.text[e.span.start : e.span.end] == e.excerpt
    ids = {f.id for f in r.findings}
    assert all(p.finding_id in ids and p.provenance.method == "template" for p in r.repairs)
    assert all(req.provenance.component == "nlp.requirements" for req in r.requirements)


def test_rewrite_guard():
    template = "Nominal cover to reinforcement shall be 45 mm, in accordance with IS 456:2000."
    assert validate_rewrite(template, "The nominal cover to the reinforcement shall be 45 mm in accordance with IS 456:2000.").ok
    assert not validate_rewrite(template, "Nominal cover shall be 40 mm in accordance with IS 456:2000.").ok
    assert not validate_rewrite(template, "Nominal cover shall be 45 mm in accordance with IS 456.").ok
    assert not validate_rewrite(template, "Nominal cover shall be 45 mm per IS 456:2000 and IS 3370.").ok
    assert not validate_rewrite("Rated [value] kA per IS/IEC 61439-1:2020.", "Rated 50 kA per IS/IEC 61439-1:2020.").ok


def test_readiness_formula():
    hit = RetrievalHit("s", "c", 1, 0.9, "", provenance("standards.rerank", "rerank", 1, []))
    mappings = [RequirementMapping("a", [hit], "retrieval"), RequirementMapping("b", [], "none")]

    def finding(kind, severity):
        return ReasoningFinding("", kind, "", "", severity, None, "", None, None, "", "", "", [], hit.provenance)

    r = compute_readiness(
        2, mappings, [finding("conflicting", "high"), finding("verified", "low"), finding("missing", "medium")], 0.35
    )
    assert r.score == 50 - 8 - 3
    assert (r.inputs["mapped"], r.inputs["high"], r.inputs["medium"], r.inputs["low"]) == (1, 1, 1, 0)
