"""Builds the frontend contract (DocumentAnalysis) from engine output.

Used for runs loaded from the database, for stateless analyses and for the
sample workspace, so all three present results identically. A *snapshot* is a
plain dict holding the camelCase wire form of a run's requirements, mappings,
findings and repairs plus run metadata.
"""

from __future__ import annotations

from typing import Any, Optional

from standardos_aiml.nlp.classify import CATEGORY_LABELS
from standardos_aiml.serialize import to_wire
from standardos_aiml.types import AnalysisResult, Corpus

MAPPING_THRESHOLD = 0.35

Snapshot = dict[str, Any]


def snapshot_from_result(result: AnalysisResult, **meta: Any) -> Snapshot:
    """``meta``: documentId, name, organization, type, analyzedAt, isSample, corpusSource."""
    return {
        **meta,
        "runId": None,
        "runStatus": "succeeded",
        "runError": None,
        "pipelineVersion": result.pipeline_version,
        "corpusVersion": result.corpus_version,
        "warnings": result.document.warnings,
        "readiness": result.readiness.score,
        "readinessFormula": result.readiness.formula,
        "applicableStandardIds": result.applicable_standard_ids,
        "graph": to_wire(result.graph),
        "requirements": to_wire(result.requirements),
        "mappings": to_wire(result.mappings),
        "findings": to_wire(result.findings),
        "repairs": to_wire(result.repairs),
        "persisted": False,
    }


def _top_mapped(mapping: Optional[dict]) -> Optional[dict]:
    if not mapping or not mapping["hits"]:
        return None
    top = mapping["hits"][0]
    if top["confidence"] >= MAPPING_THRESHOLD or mapping["basis"] == "explicit_reference":
        return top
    return None


def build_document_analysis(s: Snapshot, corpus: Corpus) -> dict[str, Any]:
    mappings = {m["requirementId"]: m for m in s["mappings"]}

    requirements = []
    for r in s["requirements"]:
        mapping = mappings.get(r["id"])
        mapped = _top_mapped(mapping)
        standard = corpus.standard(mapped["standardId"]) if mapped else None
        clause = next((c for c in standard.clauses if c.id == mapped["clauseId"]), None) if standard and mapped else None
        out: dict[str, Any] = {
            "id": r["id"],
            "text": r["text"],
            "category": CATEGORY_LABELS.get(r["category"], r["category"]),
            "standard": standard.number if standard else "No standard matched",
            "clause": (f"Clause {clause.ref} — " if clause.ref else "") + clause.heading if clause else "—",
            "certification": (standard.certification.scheme if standard else None) or "—",
            "sectionLabel": r.get("sectionLabel"),
            "basis": mapping["basis"] if mapping else "none",
            "standardId": standard.id if standard else None,
            "provenance": r.get("provenance"),
        }
        if mapped:
            out["confidence"] = mapped["confidence"]
            out["explanation"] = mapped["explanation"]
        requirements.append(out)

    findings = [
        {
            "id": f.get("dbId") or f["id"],
            "status": f["kind"],
            "title": f["title"],
            "requirement": f["requirementText"],
            "standard": f["standardLabel"],
            "reason": f["reason"],
            "severity": f["severity"],
            "action": f["action"],
            "rule": f["rule"],
            "evidence": f["evidence"],
            "provenance": f["provenance"],
            "reviewStatus": f.get("reviewStatus") or "open",
            "reviewNote": f.get("reviewNote"),
            "documentId": s["documentId"],
            "documentName": s["name"],
        }
        for f in s["findings"]
    ]

    repairs = [
        {
            "id": r.get("dbId") or r["id"],
            "original": r["original"],
            "recommended": r["recommended"],
            "evidence": r["evidenceLabel"],
            "reason": r["reason"],
            "status": r.get("status") or "pending",
            "finalText": r.get("finalText"),
            "provenance": r["provenance"],
        }
        for r in s["repairs"]
    ]

    open_findings = [f for f in s["findings"] if f["kind"] != "verified" and f.get("reviewStatus") != "dismissed"]
    schemes = {
        std.certification.scheme
        for std in (corpus.standard(i) for i in s["applicableStandardIds"])
        if std and std.certification.scheme
    }
    if s["runStatus"] == "failed":
        status = "Failed"
    elif s["runStatus"] != "succeeded":
        status = "Processing"
    else:
        status = "Review required" if any(f["severity"] != "low" for f in open_findings) else "Analyzed"

    return {
        "id": s["documentId"],
        "name": s["name"],
        "type": s["type"],
        "documentType": s.get("documentType", "specification"),
        "documentTypeLabel": s.get("documentTypeLabel") or "Technical specification",
        "organization": s["organization"],
        "analyzedAt": s["analyzedAt"],
        "standards": len(s["applicableStandardIds"]),
        "issues": len(open_findings),
        "readiness": s["readiness"],
        "status": status,
        "requirements": requirements,
        "findings": findings,
        "repairs": repairs,
        "requirementCount": len(s["requirements"]),
        "certificationCount": len(schemes),
        "graphPaths": build_graph_paths(s, corpus),
        "runId": s["runId"],
        "runStatus": s["runStatus"],
        "runError": s["runError"],
        "pipelineVersion": s["pipelineVersion"],
        "corpusVersion": s["corpusVersion"],
        "corpusSource": s.get("corpusSource"),
        "warnings": s["warnings"],
        "readinessFormula": s["readinessFormula"],
        "isSample": s["isSample"],
        "persisted": s["persisted"],
    }


def summary_of(doc: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in doc.items() if k not in ("requirements", "findings", "repairs", "graphPaths")}


def build_graph_paths(s: Snapshot, corpus: Corpus) -> list[dict[str, Any]]:
    """Requirement → standard → clause → test standard → certification paths, strongest first."""
    mappings = {m["requirementId"]: m for m in s["mappings"]}
    paths: list[dict[str, Any]] = []
    for req in s["requirements"]:
        top = _top_mapped(mappings.get(req["id"]))
        standard = corpus.standard(top["standardId"]) if top else None
        clause = next((c for c in standard.clauses if c.id == top["clauseId"]), None) if standard and top else None
        if not standard or not clause or not top:
            continue
        nodes = [
            {"id": req["id"], "kind": "requirement", "label": "Requirement", "detail": req["text"]},
            {"id": standard.id, "kind": "standard", "label": standard.number, "detail": standard.title},
            {
                "id": clause.id,
                "kind": "clause",
                "label": f"Clause {clause.ref}" if clause.ref else clause.heading,
                "detail": clause.text,
            },
        ]
        test = next((r for r in corpus.relationships if r.from_id == standard.id and r.type == "TESTED_BY"), None)
        test_std = corpus.standard(test.to_id) if test else None
        if test_std:
            nodes.append(
                {"id": test_std.id, "kind": "test", "label": test_std.number, "detail": f"Test method: {test_std.title}"}
            )
        if standard.certification.scheme:
            nodes.append(
                {
                    "id": f"cert:{standard.id}",
                    "kind": "certification",
                    "label": "BIS certification",
                    "detail": standard.certification.scheme,
                }
            )
        paths.append(
            {
                "requirementId": req["id"],
                "requirement": req["text"],
                "confidence": top["confidence"],
                "nodes": nodes,
                "_current": standard.status not in ("superseded", "withdrawn"),
            }
        )
    # Paths through current standards first, then the most informative (longest), then the strongest.
    paths.sort(key=lambda p: (-int(p["_current"]), -len(p["nodes"]), -p["confidence"]))
    for p in paths:
        del p["_current"]
    return paths
