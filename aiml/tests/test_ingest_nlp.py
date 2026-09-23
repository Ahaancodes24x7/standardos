from __future__ import annotations

import pytest

from standardos_aiml.ingest.normalize import normalize_characters, reflow_lines, strip_repeated_lines
from standardos_aiml.ingest.parse import ParseError, docx_html_to_text, parse_document
from standardos_aiml.ingest.sections import detect_sections
from standardos_aiml.nlp.entities import extract_entities, extract_standard_references, extract_text_parameters
from standardos_aiml.nlp.quantities import extract_quantities, infer_parameter
from standardos_aiml.nlp.requirements import extract_requirements, structure_fragment
from standardos_aiml.pipeline import run_pipeline
from standardos_aiml.standards.seed import seed_corpus

from .fixtures import make_docx, make_pdf


def q(text: str):
    return extract_quantities(text)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parses_text_layer_pdf():
    pdf = make_pdf(
        [["1.1 Panels shall be rated for an ambient temperature of 50 deg C.", "1.2 Degree of protection shall be IP54."]]
    )
    doc = parse_document((pdf, "spec.pdf"))
    assert doc.format == "pdf" and doc.parser == "pypdf"
    assert "ambient temperature of 50 deg C" in doc.text and "IP54" in doc.text


def test_rejects_scanned_pdf():
    with pytest.raises(ParseError) as err:
        parse_document((make_pdf([[]]), "scan.pdf"))
    assert err.value.code == "no_text_layer"


def test_docx_tables_become_attribute_lines():
    docx = make_docx(["Motor data", "The motor shall conform to IS 325."], [("Rated output", "15 kW"), ("Protection", "IP55")])
    doc = parse_document((docx, "motor.docx"))
    assert doc.format == "docx"
    assert "Rated output: 15 kW" in doc.text and "Protection: IP55" in doc.text
    result = run_pipeline(doc, seed_corpus())
    assert any(
        a.parameter == "rated_power" and a.quantity and a.quantity.value == 15000
        for r in result.requirements
        for a in r.attributes
    )


def test_txt_decoding():
    assert parse_document(("﻿Temperature 40 °C".encode("utf-8"), "a.txt")).text == "Temperature 40 °C"
    assert parse_document((b"Temperature 40 \xb0C", "b.txt")).text == "Temperature 40 °C"


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ((b"hello", "a.doc"), "unsupported_format"),
        ((b"", "a.txt"), "empty"),
        ((b"not a pdf", "a.pdf"), "corrupt"),
        ("   ", "empty"),
    ],
)
def test_rejects_bad_inputs(source, code):
    with pytest.raises(ParseError) as err:
        parse_document(source)
    assert err.value.code == code


def test_mammoth_html_conversion():
    assert "• One" in docx_html_to_text("<h1>A &amp; B</h1><ul><li>One</li><li>Two</li></ul>")
    assert "5 < 6" in docx_html_to_text("<p>5 &lt; 6</p>")


# ---------------------------------------------------------------------------
# Normalisation and sections
# ---------------------------------------------------------------------------


def test_normalisation():
    assert normalize_characters("120ºC − 5 “ok” ﬁt") == '120°C - 5 "ok" fit'


def test_reflow():
    text = reflow_lines(
        "3.1 The panel shall be\nsuitable for outdoor use.\n3.2 Degree of protection IP55.\nThe insu-\nlation shall be XLPE."
    )
    assert text == (
        "3.1 The panel shall be suitable for outdoor use.\n3.2 Degree of protection IP55.\nThe insulation shall be XLPE."
    )


def test_strips_running_headers():
    pages = [f"Tender 47\nPage {i} of 3\n{c} shall be {d}." for i, (c, d) in enumerate([("A", "B"), ("C", "D"), ("E", "F")], 1)]
    assert strip_repeated_lines(pages) == ["A shall be B.", "C shall be D.", "E shall be F."]


def test_sections():
    sections = detect_sections("4 TECHNICAL REQUIREMENTS\n4.1 The motor shall be IE3.\nGENERAL NOTES", lambda _: None)
    assert [(s.number, s.heading) for s in sections] == [("4", "TECHNICAL REQUIREMENTS"), ("4.1", ""), (None, "GENERAL NOTES")]


# ---------------------------------------------------------------------------
# Quantities
# ---------------------------------------------------------------------------


def test_units_are_canonicalised():
    assert (q("11 kV")[0].value, q("11 kV")[0].unit) == (11000, "V")
    assert (q("25 mm")[0].value, q("25 mm")[0].unit) == (25, "mm")  # regression: once read as 25 m
    assert q("45 m head")[0].value == 45000
    assert (q("2.5 sq mm")[0].value, q("2.5 sq mm")[0].unit) == (2.5, "mm2")
    assert q("20 m3/hr")[0].unit == "m3/h"
    assert q("10 lps")[0].value == pytest.approx(36)
    assert (q("25 N/mm2")[0].value, q("25 N/mm2")[0].unit) == (25, "MPa")
    assert q("15 HP")[0].value == pytest.approx(11185.5)
    assert q("104 °F")[0].value == pytest.approx(40)


def test_comparators():
    x = q("not less than 20 mm")[0]
    assert (x.comparator, x.min, x.max) == ("min", 20, None)
    x = q("shall not exceed 500 mg/l")[0]
    assert (x.comparator, x.min, x.max) == ("max", None, 500)
    assert q("1 NTU (max)")[0].comparator == "max"
    assert (q("up to 95 %")[0].comparator, q("up to 95 %")[0].max) == ("max", 95)
    assert (q("65 % or more")[0].comparator, q("65 % or more")[0].min) == ("min", 65)


def test_ranges_and_tolerances():
    x = q("-5 °C to 45 °C")[0]
    assert (x.comparator, x.min, x.max) == ("range", -5, 45)
    x = q("between 10 and 40 °C")[0]
    assert (x.comparator, x.min, x.max) == ("range", 10, 40)
    x = q("415 V ± 10 %")[0]
    assert (x.comparator, x.min, x.max, x.tolerance) == ("tolerance", 373.5, 456.5, 0.1)
    x = q("pH shall be between 6.5 and 8.5")[0]
    assert (x.unit, x.min, x.max) == ("pH", 6.5, 8.5)
    x = q("water-cement ratio shall not exceed 0.45")[0]
    assert (x.unit, x.max) == ("ratio", 0.45)


def test_identifiers_are_not_quantities():
    assert q("IP55, M25, IS 732:2019, Fe 500D") == []


def test_parameter_inference():
    text = "The motor shall operate at 415 V and deliver 15 kW at an ambient of 50 °C."
    assert [infer_parameter(text, x).key for x in q(text)] == ["rated_voltage", "rated_power", "ambient_temperature"]
    sc = "Short circuit rating of busbars: 50 kA for 1 s."
    assert infer_parameter(sc, q(sc)[0]).key == "short_circuit_rating"


# ---------------------------------------------------------------------------
# Entities and requirements
# ---------------------------------------------------------------------------


def test_designations():
    refs = extract_standard_references(
        "IS:732-2019, IS 1554 (Pt. 1):1988, IS 1554-1, IS/IEC 61439-1:2020, IEC 60529, IS 516 (Part 1/Sec 1), I.S. 3043"
    )
    assert [f"{r.designation}|{r.year or ''}" for r in refs] == [
        "IS 732|2019",
        "IS 1554 (Part 1)|1988",
        "IS 1554 (Part 1)|",
        "IS/IEC 61439-1|2020",
        "IEC 60529|",
        "IS 516 (Part 1/Sec 1)|",
        "IS 3043|",
    ]


def test_entities():
    text = "IP 55 enclosure, concrete grade M25, Fe 500D bars, copper conductor, ISI mark"
    assert [f"{e.kind}:{e.value}" for e in extract_entities(text)] == [
        "ip_rating:IP55",
        "concrete_grade:M25",
        "steel_grade:Fe 500D",
        "material:copper",
        "certification:isi mark",
    ]
    assert extract_entities("M20 bolts") == []
    values = [p.value for p in extract_text_parameters("IE3 motors with class F insulation for S1 duty, severe exposure")]
    assert values == ["IE3", "Class F", "S1", "severe"]


@pytest.mark.parametrize(
    "text", ["Wires shall be ISI marked.", "Wires shall bear ISI marking.", "Motors shall bear the ISI mark."]
)
def test_isi_mark_variants_are_conformity_evidence(text):
    # Regression: "ISI marked" (the usual tender wording) was not recognised (found by the benchmark).
    assert [(e.kind, e.value) for e in extract_entities(text)] == [("certification", "isi mark")]


def extract(text: str):
    return extract_requirements(text, detect_sections(text, lambda _: None), lambda _: None)


def test_identifies_requirements_and_skips_boilerplate():
    reqs = extract(
        "TECHNICAL SPECIFICATION\nTender No. 12/2026\n1. General\n1.1 Panels shall be floor mounted.\n"
        "1.2 Rated voltage: 415 V\nNote: drawings are indicative.\n1.3 Cables should be copper."
    )
    assert [r.text for r in reqs] == ["Panels shall be floor mounted.", "Rated voltage: 415 V", "Cables should be copper."]
    assert [r.modality for r in reqs] == ["mandatory", "declarative", "recommended"]


def test_clause_labels_and_provenance():
    (req,) = extract("3 ELECTRICAL\n3.2 Busbars shall be rated for 800 A.")
    assert "3.2" in req.section_label
    assert (req.provenance.component, req.provenance.method) == ("nlp.requirements", "rule")
    assert "shall" in " ".join(req.provenance.signals)


def test_vague_requirements():
    (req,) = extract("The pump shall be energy efficient.")
    assert req.vague
    eff = next(a for a in req.attributes if a.parameter == "efficiency")
    assert eff.quantity is None and eff.text is None


def test_voltage_variation_from_tolerance():
    f = structure_fragment("Motor suitable for 415 V ± 15 %, 50 Hz")
    assert next(a for a in f.attributes if a.parameter == "voltage_variation").quantity.value == 15
    assert f.category == "electrical"
