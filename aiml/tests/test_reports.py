"""Non-specification documents: tables, test / inspection reports, datasheets and BOQs.

The API runs these with the flags below (backend/app/doctypes.config_for); specifications
never set them, so their behaviour and every recorded evaluation are unchanged.
"""

from standardos_aiml.config import preset
from standardos_aiml.ingest.tables import linearize_tables
from standardos_aiml.pipeline import run_pipeline
from standardos_aiml.standards.seed import seed_corpus

corpus = seed_corpus()


def run(text: str, role: str):
    cfg = preset("v3.1").with_(zoning=False, tables_v2=True, reports_v1=True, document_role=role)
    return run_pipeline(text, corpus, config=cfg)


def problems(result):
    return [f for f in result.findings if f.kind != "verified"]


WATER = """TEST REPORT — DRINKING WATER
Method: IS 3025; bacteriological as per IS 1622
Parameter | Unit | Result | Acceptable limit (IS 10500:2012)
pH | - | 7.4 | 6.5 - 8.5
Turbidity | NTU | 3.2 | 1
Total dissolved solids | mg/l | 640 | 500
Nitrate | mg/l | 38 | 45
"""


def test_tables_become_statements_with_units():
    lines = [l for l in linearize_tables(WATER).split("\n") if l]
    assert "Turbidity: acceptable limit (IS 10500:2012) 1 NTU; result 3.2 NTU." in lines
    gtp = linearize_tables("Sl. No. | Particulars | Unit | Offered\n1 | Rated power | kVA | 630\n")
    assert "Rated power: 630 kVA." in gtp
    boq = linearize_tables("Item | Description | Unit | Qty\n2 | 3.5 core 300 sq mm cable to IS 7098 (Part 1) | m | 480\n")
    assert "Item 2: 3.5 core 300 sq mm cable to IS 7098 (Part 1) (quantity 480 m)." in boq


def test_lab_report_results_are_checked_against_the_standard():
    r = run(WATER, "report")
    flagged = {f.parameter for f in problems(r) if f.kind == "conflicting"}
    assert flagged == {"turbidity", "tds"}  # nitrate and pH are within limits; "10500" is not a pH value


def test_measured_results_against_limits_stated_in_the_report():
    r = run(
        "SITE INSPECTION REPORT — EARTHING\n"
        "Earth pit 1: measured earth resistance 2.4 ohm.\n"
        "Earth pit 2: measured earth resistance 0.7 ohm.\n"
        "Specified earth resistance: not more than 1 ohm.\n"
        "Conclusion: earth resistance exceeds the specified value.\n",
        "report",
    )
    found = problems(r)
    assert [f.rule for f in found] == ["result_nonconformity"]  # pit 1 only; the conclusion is not double-counted
    assert "2.4" in found[0].title and found[0].severity == "high"


def test_report_is_not_judged_as_a_specification():
    r = run(
        "PRE-DISPATCH INSPECTION REPORT\n"
        "Guaranteed duty point: 450 m3/h at 42 m total head, efficiency 80 %.\n"
        "Measured at duty point: discharge 452 m3/h, total head 41.6 m, pump efficiency 78.5 %.\n"
        "Motor: 75 kW, 415 V, squirrel cage induction motor to IS 325:1996, IE3.\n",
        "report",
    )
    rules = {f.rule for f in problems(r)}
    assert rules == {"result_nonconformity"}  # no checklist / dependency / certification gaps
    by_param = {f.parameter: f.severity for f in problems(r)}
    assert by_param == {"efficiency": "medium", "pump_head": "low"}  # 1 % head shortfall: check tolerance


def test_declared_failures_and_passing_reports():
    fail = run(
        "S.No. | Test | Specified value | Measured value | Remarks\n"
        "1 | High voltage test | 3 kV, 5 min | Breakdown at 2 min | Fail\n",
        "report",
    )
    assert [f.rule for f in problems(fail)] == ["reported_nonconformity"]
    ok = run(
        "Parameter | Guaranteed | Measured\n"
        "Full load efficiency | 93.0 % | 93.3 %\n"
        "Noise level at 1 m | 85 dB(A) | 83 dB(A)\n",
        "report",
    )
    assert problems(ok) == [] and ok.readiness.score == 100


def test_test_voltages_losses_and_temperature_rise_are_not_ratings():
    r = run(
        "Parameter | Unit | Value\n"
        "Temperature rise of top oil | deg C | 45\n"
        "Total losses at 50% load | W | 3400\n"
        "Power-frequency withstand | kV | 2.5\n"
        "Short-time withstand | kA | 50 for 1 s\n",
        "declaration",
    )
    params = {a.parameter for q in r.requirements for a in q.attributes}
    assert params == {"short_circuit_rating"}  # no ambient / power rating / voltage rating / frequency


def test_boq_keeps_outdated_reference_checks_only():
    r = run(
        "Item | Description | Unit | Qty\n"
        "1 | MCBs conforming to IS 8828, 10 kA breaking capacity | No. | 60\n"
        "2 | 3.5 core 300 sq mm XLPE cable conforming to IS 7098 (Part 1):1988 | m | 480\n",
        "schedule",
    )
    assert {f.rule for f in problems(r)} == {"superseded_reference"}
    assert len(r.requirements) == 2
