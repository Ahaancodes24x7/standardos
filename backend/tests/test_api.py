"""End-to-end API tests against Postgres: auth, upload → run → results, review, audit, report, isolation."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from .conftest import TEST_URL, sign_up
from .fixtures import make_docx, make_pdf

pytestmark = pytest.mark.skipif(not TEST_URL, reason="TEST_DATABASE_URL is not set")

PANEL_SPEC = """TECHNICAL SPECIFICATION FOR LT PANELS
1. Panels shall conform to IS 8623:1993.
2. Panels shall be rated for operation at an ambient temperature of 120°C.
3. The rated operational voltage shall be 415 V, 3 phase, 50 Hz.
4. Tests shall be carried out as per relevant IS.
"""


def analyse_text(client: TestClient, text: str) -> tuple[str, str]:
    res = client.post("/api/analyses", data={"text": text})
    assert res.status_code == 200, res.text
    body = res.json()
    return body["documentId"], body["runId"]


# ---------------------------------------------------------------------------


def test_health_and_public_standards(client: TestClient):
    health = client.get("/api/health").json()
    assert health["ok"] and health["database"] and health["corpusSource"] == "database"
    standards = client.get("/api/standards").json()
    assert len(standards) == 39
    detail = client.get("/api/standards/is-732-2019").json()
    assert detail["number"].startswith("IS 732") and detail["clauses"]
    assert client.get("/api/standards/does-not-exist").status_code == 404
    graph = client.get("/api/standards/is-iec-61439-1-2020/graph", params={"depth": 2}).json()
    assert graph["nodes"][0]["id"] == "is-iec-61439-1-2020" and graph["edges"]
    status = client.get("/api/corpus/status").json()
    assert status["source"] == "database" and status["clauses"] == 90


def test_search(client: TestClient):
    results = client.post(
        "/api/standards/search", json={"query": "Earth electrode resistance shall not exceed 1 ohm"}
    ).json()
    assert results and results[0]["standard"]["id"].startswith("is-3043")
    filtered = client.post(
        "/api/standards/search", json={"query": "PVC insulated cables", "yearRanges": ["-2009"]}
    ).json()
    assert all(r["standard"]["year"] < 2010 for r in filtered)


def test_auth_flow(client: TestClient):
    assert client.get("/api/auth/me").json() is None
    user = sign_up(client, "Asha")
    me = client.get("/api/auth/me").json()
    assert me["email"] == user["email"] and me["profile"]["organization"] == "Test Cell"
    dup = client.post(
        "/api/auth/signup",
        json={"email": user["email"], "password": "another password", "fullName": "X", "organization": "Y"},
    )
    assert dup.status_code == 400 and "already exists" in dup.json()["detail"]
    assert client.patch("/api/auth/profile", json={"fullName": "Asha K", "organization": "PWD"}).status_code == 200
    assert client.get("/api/auth/me").json()["profile"]["full_name"] == "Asha K"
    client.post("/api/auth/signout")
    assert client.get("/api/auth/me").json() is None
    bad = client.post("/api/auth/signin", json={"email": user["email"], "password": "wrong password"})
    assert bad.status_code == 401
    ok = client.post("/api/auth/signin", json={"email": user["email"], "password": "correct horse battery"})
    assert ok.status_code == 200
    # Password reset round trip.
    reset = client.post("/api/auth/password-reset/request", json={"email": user["email"]}).json()
    token = reset["resetUrl"].split("token=")[1]
    assert client.post("/api/auth/password-reset/confirm", json={"token": token, "password": "new password 1"}).status_code == 200
    assert client.post("/api/auth/password-reset/confirm", json={"token": token, "password": "new password 2"}).status_code == 400
    assert client.post("/api/auth/signin", json={"email": user["email"], "password": "new password 1"}).status_code == 200
    # Unknown emails get the same answer and no link.
    assert client.post("/api/auth/password-reset/request", json={"email": "nobody@example.com"}).json() == {"ok": True}


def test_protected_endpoints_require_session(client: TestClient):
    assert client.get("/api/documents").status_code == 401
    assert client.post("/api/analyses", data={"text": PANEL_SPEC}).status_code == 401


def test_upload_run_results_review_audit_report(client: TestClient):
    sign_up(client)
    document_id, run_id = analyse_text(client, PANEL_SPEC)

    # TestClient runs background tasks before returning, so the run is complete.
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["status"] == "succeeded" and run["stage"] == 8

    doc = client.get(f"/api/documents/{document_id}").json()
    assert doc["persisted"] and doc["runStatus"] == "succeeded" and doc["status"] == "Review required"
    assert doc["requirementCount"] == 4 and doc["corpusSource"] == "database"
    rules = {f["rule"] for f in doc["findings"]}
    assert {"constraint_conflict", "superseded_reference"} <= rules
    conflict = next(f for f in doc["findings"] if f["rule"] == "constraint_conflict")
    assert conflict["evidence"] and conflict["provenance"]["component"] == "reasoning.conflicts"
    uuid.UUID(conflict["id"])  # database id, not the local "f-1"

    # Filtered findings API (gap / conflict APIs).
    conflicts = client.get("/api/findings", params={"kind": "conflicting", "documentId": document_id}).json()
    assert conflicts and all(f["status"] == "conflicting" for f in conflicts)
    assert client.get(f"/api/findings/{conflict['id']}").json()["title"] == conflict["title"]

    # Human review and repair decisions are persisted and audited.
    res = client.post(f"/api/findings/{conflict['id']}/review", json={"status": "confirmed", "note": "Site is 45 °C"})
    assert res.status_code == 200
    repair = doc["repairs"][0]
    assert client.post(f"/api/repairs/{repair['id']}/decision", json={"decision": "edited"}).status_code == 400
    edited = client.post(
        f"/api/repairs/{repair['id']}/decision", json={"decision": "edited", "text": "Panels shall be rated for 45 °C."}
    ).json()
    assert edited == {"status": "edited", "finalText": "Panels shall be rated for 45 °C."}

    reloaded = client.get(f"/api/documents/{document_id}").json()
    assert next(f for f in reloaded["findings"] if f["id"] == conflict["id"])["reviewStatus"] == "confirmed"
    assert next(r for r in reloaded["repairs"] if r["id"] == repair["id"])["status"] == "edited"

    actions = [e["action"] for e in client.get(f"/api/documents/{document_id}/audit").json()]
    assert {"uploaded", "queued", "succeeded", "review:confirmed", "repair:edited"} <= set(actions)

    report = client.get(f"/api/documents/{document_id}/report").json()
    assert report["filename"].endswith("-compliance-report.md")
    assert "Adopted text:** Panels shall be rated for 45 °C." in report["markdown"]

    listing = client.get("/api/documents").json()
    assert [d["id"] for d in listing] == [document_id]
    summaries = client.get("/api/documents", params={"summary": "true"}).json()
    assert "findings" not in summaries[0] and summaries[0]["issues"] > 0

    impact = client.get("/api/change-impact").json()
    assert any(any(a["documentId"] == document_id for a in e["affected"]) for e in impact)

    # Re-analysis creates a new run; results come from the latest run.
    rerun = client.post(f"/api/documents/{document_id}/reanalyze").json()
    assert client.get(f"/api/runs/{rerun['runId']}").json()["status"] == "succeeded"
    assert client.get(f"/api/documents/{document_id}").json()["runId"] == rerun["runId"]
    # Executing an already finished run is a no-op that reports its status.
    assert client.post(f"/api/runs/{run_id}/execute").json() == {"status": "succeeded"}


def test_owner_isolation(client: TestClient):
    sign_up(client, "Owner")
    document_id, run_id = analyse_text(client, PANEL_SPEC)
    finding_id = client.get(f"/api/documents/{document_id}").json()["findings"][0]["id"]
    client.post("/api/auth/signout")
    sign_up(client, "Intruder")
    assert client.get(f"/api/documents/{document_id}").status_code == 404
    assert client.get(f"/api/runs/{run_id}").status_code == 404
    assert client.post(f"/api/findings/{finding_id}/review", json={"status": "dismissed"}).status_code == 404
    assert client.get("/api/documents").json() == []


def test_pdf_docx_and_failures(client: TestClient):
    sign_up(client)
    pdf = make_pdf(
        [
            ["SUPPLY OF SUBMERSIBLE PUMPSETS", "1. Pumpsets shall conform to IS 8034.", "2. Rated discharge: 36 m3/h."],
            ["3. Total head: 60 m.", "4. Motor shall be suitable for 415 V, 50 Hz supply."],
        ]
    )
    res = client.post("/api/analyses", files={"file": ("pumps.pdf", pdf, "application/pdf")})
    doc = client.get(f"/api/documents/{res.json()['documentId']}").json()
    assert doc["type"] == "PDF" and doc["runStatus"] == "succeeded" and doc["requirementCount"] >= 4

    docx = make_docx(["The earthing shall conform to IS 3043."], [("Earth resistance", "not more than 1 ohm")])
    res = client.post(
        "/api/analyses",
        files={"file": ("earthing.docx", docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    doc = client.get(f"/api/documents/{res.json()['documentId']}").json()
    assert doc["type"] == "DOCX" and any("Earth resistance" in r["text"] for r in doc["requirements"])

    scanned = make_pdf([[], []])
    res = client.post("/api/analyses", files={"file": ("scan.pdf", scanned, "application/pdf")})
    run = client.get(f"/api/runs/{res.json()['runId']}").json()
    assert run["status"] == "failed" and run["errorCode"] == "no_text_layer"
    assert client.get(f"/api/documents/{res.json()['documentId']}").json()["status"] == "Failed"

    bad = client.post("/api/analyses", files={"file": ("spec.xlsx", b"PK\x03\x04", "application/octet-stream")})
    assert bad.status_code == 400 and "Unsupported" in bad.json()["detail"]
    assert client.post("/api/analyses", data={"text": "   "}).status_code == 400


def test_demo_endpoints_need_no_account(client: TestClient):
    samples = client.get("/api/samples").json()
    assert len(samples) == 3 and all(s["isSample"] and not s["persisted"] for s in samples)
    doc = client.post("/api/analyze/stateless", data={"text": PANEL_SPEC}).json()
    assert doc["id"].startswith("local-") and doc["findings"]
    impact = client.get("/api/change-impact", params={"scope": "sample"}).json()
    assert any(e["affected"] for e in impact)


def test_sweeper(client: TestClient):
    assert client.get("/api/cron/analysis-sweeper").status_code == 401
    res = client.get("/api/cron/analysis-sweeper", headers={"Authorization": "Bearer cron-test-secret"})
    assert res.status_code == 200 and set(res.json()) == {"requeued", "failed", "executed"}


def test_engine_dag_and_evaluation(client: TestClient):
    engine = client.get("/api/engine").json()
    assert engine["pipelineVersion"].startswith("standardos-pipeline/3.") and engine["config"] == "v3.1"

    dag = client.get("/api/dependency-dag").json()
    assert dag["cycles"] == [] and dag["stats"]["nodes"] > 0 and dag["edges"]
    deps = client.get("/api/standards/is-456-2000/dependencies").json()
    assert {"is-269-2015", "is-1786-2008"} <= {d["id"] for d in deps["dependsOn"]}
    assert [d["id"] for d in client.get("/api/standards/is-269-2015/dependencies").json()["requiredBy"]] == ["is-456-2000"]
    assert client.get("/api/standards/nope/dependencies").status_code == 404

    runs = client.get("/api/evaluation/runs").json()
    if runs:  # present in a checkout with aiml/results
        assert runs[0]["documents"] and "fnd_f1" in runs[0]["documents"][0]["metrics"]
        assert client.get(f"/api/evaluation/runs/{runs[0]['runId']}").json()["tasks"]
    assert client.get("/api/evaluation/runs/..%2F..%2Fetc").status_code == 404


def test_change_impact_follows_dag(client: TestClient):
    sign_up(client, "Civil")
    document_id, _ = analyse_text(
        client,
        "SPECIFICATION FOR RCC WORKS\n1. All reinforced concrete shall conform to IS 456:2000.\n"
        "2. Concrete grade shall be M25 for moderate exposure.\n",
    )
    impact = {e["standardId"]: e for e in client.get("/api/change-impact").json()}
    # Directly affected: the dependency-gap finding names IS 269 as evidence.
    assert any(a["documentId"] == document_id for a in impact["is-269-2015"]["affected"])

    # Indirect: a document that only maps to IS 456 is affected by an IS 269 change through the DAG.
    from standardos_aiml.pipeline import get_engine

    from app.corpus import get_corpus
    from app.routers.standards import _affected

    corpus = get_corpus().corpus
    doc = {"name": "RCC spec", "id": "d1", "isSample": False, "runStatus": "succeeded",
           "requirements": [{"standardId": "is-456-2000"}], "findings": []}
    assert _affected([doc], "is-269-2015", get_engine(corpus).dag, corpus) == [
        {"name": "RCC spec", "documentId": "d1", "via": "IS 456:2000"}
    ]
    assert _affected([doc], "is-3043-2018", get_engine(corpus).dag, corpus) == []


def test_corpus_import_requires_admin(client: TestClient):
    sign_up(client, "NotAdmin")
    res = client.post("/api/admin/corpus/import", files={"file": ("c.json", b"{}", "application/json")})
    assert res.status_code == 403


BOQ = """SCHEDULE OF QUANTITIES
1 | Supply of LT panel with 1600 A ACB incomer, 50 kA, IP54, conforming to IS/IEC 61439-2:2020 | No. | 1
2. Supply of 3.5 core 300 sq mm XLPE armoured cable conforming to IS 7098 (Part 1):1988 | m | 480
3. MCBs conforming to IS 8828, 10 kA breaking capacity | No. | 60
"""


def test_document_types(client: TestClient):
    sign_up(client, "Types")
    types = client.get("/api/document-types").json()
    assert {t["key"] for t in types} >= {"specification", "boq", "datasheet", "test_report", "other"}

    # A BOQ is analysed as a schedule: zoning must not drop it.
    res = client.post("/api/analyses", data={"text": BOQ, "documentType": "boq"})
    assert res.status_code == 200, res.text
    boq_id, run_id = res.json()["documentId"], res.json()["runId"]
    assert client.post(f"/api/runs/{run_id}/execute").json()["status"] == "succeeded"
    boq = client.get(f"/api/documents/{boq_id}").json()
    assert boq["documentType"] == "boq" and boq["documentTypeLabel"] == "Bill of quantities"
    assert boq["requirementCount"] >= 2
    assert any(f["status"] == "outdated" for f in boq["findings"])  # IS 8828 is withdrawn

    # Custom type needs a name; unknown types are rejected.
    assert client.post("/api/analyses", data={"text": PANEL_SPEC, "documentType": "other"}).status_code == 400
    assert client.post("/api/analyses", data={"text": PANEL_SPEC, "documentType": "poem"}).status_code == 400
    custom = client.post(
        "/api/analyses", data={"text": PANEL_SPEC, "documentType": "other", "documentTypeLabel": "Consultant review note"}
    ).json()
    client.post(f"/api/runs/{custom['runId']}/execute")
    doc = client.get(f"/api/documents/{custom['documentId']}").json()
    assert doc["documentType"] == "other" and doc["documentTypeLabel"] == "Consultant review note"

    # Re-typing to a type that reads the document differently queues a new run.
    patched = client.patch(f"/api/documents/{custom['documentId']}", json={"documentType": "specification", "name": "Panel spec"}).json()
    assert patched["runId"]
    client.post(f"/api/runs/{patched['runId']}/execute")
    doc = client.get(f"/api/documents/{custom['documentId']}").json()
    assert doc["name"] == "Panel spec" and doc["documentType"] == "specification" and doc["runId"] == patched["runId"]
    assert client.patch(f"/api/documents/{custom['documentId']}", json={"name": "Renamed"}).json() == {"runId": None}
    assert "updated" in {a["action"] for a in client.get(f"/api/documents/{custom['documentId']}/audit").json()}

    # Delete removes the document and everything under it.
    assert client.delete(f"/api/documents/{boq_id}").json() == {"deleted": True}
    assert client.get(f"/api/documents/{boq_id}").status_code == 404
    assert client.delete(f"/api/documents/{boq_id}").status_code == 404


def test_stale_run_is_reclaimed(client: TestClient):
    """A run frozen mid-flight (serverless) is re-executed by the next /execute call."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import update

    from app import models as m
    from app.db import session_scope

    sign_up(client, "Stale")
    document_id, run_id = analyse_text(client, PANEL_SPEC)
    with session_scope() as db:
        db.execute(
            update(m.AnalysisRun).where(m.AnalysisRun.id == uuid.UUID(run_id)).values(
                status="running", attempts=1, heartbeat_at=datetime.now(timezone.utc) - timedelta(minutes=5)
            )
        )
        db.commit()
    assert client.post(f"/api/runs/{run_id}/execute").json()["status"] == "succeeded"
    assert client.get(f"/api/documents/{document_id}").json()["runStatus"] == "succeeded"
