"""Domain types for the StandardOS intelligence engine.

Everything under ``standardos_aiml`` is pure Python with no database, network
or web-framework imports, so the same code runs in the FastAPI backend, the
evaluation harness, the benchmark and the unit tests.

Attribute names are snake_case in Python. ``standardos_aiml.serialize.to_wire``
renders them as camelCase, which is the JSON contract the frontend and the
database jsonb columns use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

DerivationMethod = Literal["rule", "lexicon", "bm25", "rerank", "graph", "constraint", "template", "llm", "model"]


@dataclass
class Provenance:
    """Attached to every AI-derived object so a reviewer can see why it exists."""

    component: str
    component_version: str
    method: str
    confidence: float
    signals: list[str]
    model: Optional[str] = None

    OMIT_NONE = frozenset({"model"})


# ---------------------------------------------------------------------------
# Phase 1 — documents and requirements
# ---------------------------------------------------------------------------

SourceFormat = Literal["pdf", "docx", "txt", "text"]


@dataclass
class TextSpan:
    start: int
    end: int


@dataclass
class ParsedPage:
    number: int
    text: str


@dataclass
class ParsedDocument:
    format: str
    parser: str
    pages: list[ParsedPage]
    text: str
    warnings: list[str]


@dataclass
class Section:
    id: str
    number: Optional[str]
    heading: str
    level: int
    span: TextSpan
    page: Optional[int]


@dataclass
class Quantity:
    """A numeric constraint in canonical units. ``min``/``max`` are inclusive bounds."""

    raw: str
    span: TextSpan
    value: Optional[float]
    min: Optional[float]
    max: Optional[float]
    unit: str
    dimension: str
    comparator: str  # eq | min | max | range | tolerance
    tolerance: Optional[float]


@dataclass
class StandardReference:
    raw: str
    span: TextSpan
    designation: str
    year: Optional[int]


@dataclass
class Entity:
    kind: str  # ip_rating | concrete_grade | steel_grade | material | product | certification | test
    value: str
    raw: str
    span: TextSpan


REQUIREMENT_CATEGORIES = [
    "performance",
    "electrical",
    "environmental",
    "safety",
    "material",
    "dimensional",
    "testing",
    "certification",
    "documentation",
    "installation",
    "quality",
    "general",
]


@dataclass
class Attribute:
    """A parameter asserted by a requirement, e.g. operating_voltage = 415 V ±10%."""

    parameter: str
    quantity: Optional[Quantity]
    text: Optional[str]


@dataclass
class StructuredRequirement:
    id: str
    text: str
    span: TextSpan
    section_id: Optional[str]
    section_label: Optional[str]
    page: Optional[int]
    modality: str
    category: str
    category_scores: dict[str, float]
    quantities: list[Quantity]
    references: list[StandardReference]
    entities: list[Entity]
    attributes: list[Attribute]
    terms: list[str]
    vague: bool
    provenance: Provenance


# ---------------------------------------------------------------------------
# Phase 2 — standards corpus and knowledge graph
# ---------------------------------------------------------------------------

RELATIONSHIP_TYPES = ["REFERENCES", "REQUIRES", "TESTED_BY", "SUPPORTS", "SUPERSEDES", "AMENDED_BY", "RELATED_TO"]


@dataclass
class ClauseConstraint:
    parameter: str
    dimension: str
    unit: str
    min: Optional[float]
    max: Optional[float]
    condition: str
    qualifier: Optional[str] = None

    OMIT_NONE = frozenset({"qualifier"})


@dataclass
class ChecklistItem:
    parameter: str
    label: str
    rationale: str
    clause_id: str
    severity: str
    repair_template: str


@dataclass
class CorpusClause:
    id: str
    standard_id: str
    ref: Optional[str]
    heading: str
    text: str
    constraints: list[ClauseConstraint]


@dataclass
class Certification:
    scheme: Optional[str]
    bodies: list[str]
    relevance: str


@dataclass
class SourceInfo:
    kind: str
    verified: bool
    note: str


@dataclass
class CorpusStandard:
    id: str
    designation: str
    year: int
    number: str
    title: str
    scope: str
    category: str
    kind: str  # product | code_of_practice | test_method | specification | terminology
    status: str  # current | amended | reaffirmed | superseded | withdrawn
    aliases: list[str]
    keywords: list[str]
    certification: Certification
    checklist: list[ChecklistItem]
    clauses: list[CorpusClause]
    source: SourceInfo


@dataclass
class CorpusRelationship:
    id: str
    type: str
    from_id: str
    to_id: str
    clause_id: Optional[str]
    confidence: float
    method: str
    note: str


@dataclass
class VersionEvent:
    id: str
    standard_id: str
    date: Optional[str]
    kind: str
    summary: str
    severity: str
    replaced_by_id: Optional[str] = None

    OMIT_NONE = frozenset({"replaced_by_id"})


@dataclass
class PriorEdition:
    designation: str
    year: int
    replaced_by_id: str


@dataclass
class Corpus:
    version: str
    standards: list[CorpusStandard]
    relationships: list[CorpusRelationship]
    events: list[VersionEvent]
    prior_editions: list[PriorEdition]
    _by_id: dict[str, CorpusStandard] = field(default_factory=dict, repr=False, compare=False)

    OMIT = frozenset({"_by_id"})

    def standard(self, standard_id: Optional[str]) -> Optional[CorpusStandard]:
        if not standard_id:
            return None
        if not self._by_id:
            self._by_id = {s.id: s for s in self.standards}
        return self._by_id.get(standard_id)


@dataclass
class RetrievalHit:
    standard_id: str
    clause_id: str
    score: float
    confidence: float
    explanation: str
    provenance: Provenance


@dataclass
class RequirementMapping:
    requirement_id: str
    hits: list[RetrievalHit]
    basis: str  # explicit_reference | retrieval | none


# ---------------------------------------------------------------------------
# Phase 3 — reasoning, findings, repairs
# ---------------------------------------------------------------------------


@dataclass
class Evidence:
    kind: str  # requirement_text | standard_clause | graph_path | constraint_check | version_record
    label: str
    excerpt: str
    requirement_id: Optional[str] = None
    span: Optional[TextSpan] = None
    standard_id: Optional[str] = None
    clause_id: Optional[str] = None
    relationship_ids: Optional[list[str]] = None

    OMIT_NONE = frozenset({"requirement_id", "span", "standard_id", "clause_id", "relationship_ids"})


@dataclass
class ReasoningFinding:
    id: str
    kind: str  # verified | missing | conflicting | outdated | certification
    rule: str
    title: str
    severity: str
    requirement_id: Optional[str]
    requirement_text: str
    standard_id: Optional[str]
    clause_id: Optional[str]
    standard_label: str
    reason: str
    action: str
    evidence: list[Evidence]
    provenance: Provenance
    parameter: Optional[str] = None

    OMIT_NONE = frozenset({"parameter"})


@dataclass
class RepairProposal:
    id: str
    finding_id: str
    original: str
    recommended: str
    evidence_label: str
    reason: str
    provenance: Provenance


STAGES = ["reading", "extracting", "categorising", "mapping", "resolving", "certifications", "conflicts", "reporting"]


@dataclass
class GraphNode:
    id: str
    kind: str
    label: str
    detail: str


@dataclass
class GraphEdge:
    id: str
    type: str
    from_: str
    to: str
    confidence: float
    provenance: str

    WIRE_NAMES = {"from_": "from"}


@dataclass
class AnalysisGraph:
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@dataclass
class Readiness:
    score: int
    formula: str
    inputs: dict[str, float]


@dataclass
class AnalysisResult:
    pipeline_version: str
    corpus_version: str
    document: ParsedDocument
    sections: list[Section]
    requirements: list[StructuredRequirement]
    mappings: list[RequirementMapping]
    applicable_standard_ids: list[str]
    graph: AnalysisGraph
    findings: list[ReasoningFinding]
    repairs: list[RepairProposal]
    readiness: Readiness
    timings_ms: dict[str, float]
