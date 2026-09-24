"""Document types: users can analyse and keep any procurement document, not only specifications.

The type is stored with the document, shown in the workspace, and steers the pipeline
where a document's layout differs from a specification's:

* a bill of quantities *is* a schedule, so zoning must not drop schedule sections and
  table rows as it does for the commercial parts of a tender;
* vendor datasheets and test / inspection reports are lists of declared or measured
  values, with no instructions to bidders or commercial conditions to exclude.

Every type runs the same engine and gets the same findings (conflicts against the
standards, gaps, dependencies, outdated references, certification).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from standardos_aiml.config import PipelineConfig

from .errors import AppError


@dataclass(frozen=True)
class DocumentType:
    key: str
    label: str
    description: str
    zoning: bool  # exclude ITB / commercial / schedule zones (specification-style documents)


DOCUMENT_TYPES: dict[str, DocumentType] = {
    t.key: t
    for t in [
        DocumentType("specification", "Technical specification", "Technical specification or requirements section.", True),
        DocumentType("tender", "Tender document", "Complete tender / NIT with bidding and commercial sections.", True),
        DocumentType("boq", "Bill of quantities", "Schedule of quantities with item descriptions.", False),
        DocumentType("datasheet", "Vendor datasheet", "Manufacturer datasheet or guaranteed technical particulars.", False),
        DocumentType("test_report", "Test report", "Type, routine or laboratory test report.", False),
        DocumentType("inspection_report", "Inspection report", "Site or pre-dispatch inspection report.", False),
        DocumentType("other", "Other", "Any other document; name its type.", False),
    ]
}
DEFAULT_TYPE = "specification"
MAX_LABEL = 60


def validate(key: Optional[str], label: Optional[str]) -> tuple[str, Optional[str]]:
    """Normalise a (type, custom label) pair from a request."""
    key = (key or DEFAULT_TYPE).strip().lower()
    if key not in DOCUMENT_TYPES:
        raise AppError(f"Unknown document type. Choose one of: {', '.join(DOCUMENT_TYPES)}.")
    label = (label or "").strip() or None
    if key == "other" and not label:
        raise AppError("Name the document type when you choose Other.")
    if label and len(label) > MAX_LABEL:
        raise AppError(f"Document type names are limited to {MAX_LABEL} characters.")
    return key, (label if key == "other" else None)


def display_label(key: str, label: Optional[str]) -> str:
    return label or DOCUMENT_TYPES.get(key, DOCUMENT_TYPES[DEFAULT_TYPE]).label


def config_for(base: PipelineConfig, key: str) -> PipelineConfig:
    doc_type = DOCUMENT_TYPES.get(key, DOCUMENT_TYPES[DEFAULT_TYPE])
    return base if doc_type.zoning or not base.zoning else base.with_(zoning=False)


def catalogue() -> list[dict[str, str]]:
    return [{"key": t.key, "label": t.label, "description": t.description} for t in DOCUMENT_TYPES.values()]
