// API contract between the frontend and the StandardOS backend (FastAPI,
// backend/app). The JSON is produced by backend/app/view.py from the Python
// engine in aiml/.
//
// These types preserve the shapes the UI was first built against. Fields
// added for the real backend — provenance, evidence, review state — are
// optional extensions, so existing components keep working unchanged.

/** How a result was produced; attached to every AI-derived object. */
export type Provenance = {
  /** Component that produced the result, e.g. "nlp.requirements". */
  component: string;
  componentVersion: string;
  method:
    "rule" | "lexicon" | "bm25" | "rerank" | "graph" | "constraint" | "template" | "llm" | "model";
  /** Model identifier when method is "llm". */
  model?: string;
  /** Confidence in [0,1]; not a calibrated probability. */
  confidence: number;
  /** Human-readable trace of the signals behind the result. */
  signals: string[];
};

export type Evidence = {
  kind:
    "requirement_text" | "standard_clause" | "graph_path" | "constraint_check" | "version_record";
  label: string;
  excerpt: string;
  requirementId?: string;
  span?: { start: number; end: number };
  standardId?: string;
  clauseId?: string;
  relationshipIds?: string[];
};

export type FindingStatus = "verified" | "missing" | "conflicting" | "outdated" | "certification";
export type Severity = "low" | "medium" | "high";
export type ReviewStatus = "open" | "confirmed" | "dismissed";
export type RepairStatus = "pending" | "accepted" | "rejected" | "edited";
export type RunStatus = "queued" | "running" | "succeeded" | "failed";

export type Finding = {
  id: string;
  status: FindingStatus;
  title: string;
  requirement: string;
  standard: string;
  reason: string;
  severity: Severity;
  action: string;
  // --- extensions ---
  rule?: string;
  evidence?: Evidence[];
  provenance?: Provenance;
  reviewStatus?: ReviewStatus;
  reviewNote?: string | null;
  documentId?: string;
  documentName?: string;
};

export type Requirement = {
  id: string;
  text: string;
  category: string;
  standard: string;
  clause: string;
  certification: string;
  // --- extensions ---
  sectionLabel?: string | null;
  confidence?: number;
  explanation?: string;
  basis?: "explicit_reference" | "retrieval" | "none";
  standardId?: string | null;
  provenance?: Provenance;
};

export type Repair = {
  id: string;
  original: string;
  recommended: string;
  evidence: string;
  reason: string;
  // --- extensions ---
  status?: RepairStatus;
  finalText?: string | null;
  provenance?: Provenance;
};

export type GraphPathNode = {
  id: string;
  kind: "requirement" | "standard" | "clause" | "test" | "certification";
  label: string;
  detail: string;
};
export type GraphPath = {
  requirementId: string;
  requirement: string;
  confidence: number;
  nodes: GraphPathNode[];
};

/** Wire format of an analysed document. `analyzedAt` is ISO-8601 on the wire. */
export type DocumentAnalysis = {
  id: string;
  name: string;
  type: string;
  organization: string;
  analyzedAt: string;
  standards: number;
  issues: number;
  readiness: number;
  status: "Analyzed" | "Review required" | "Processing" | "Failed";
  requirements: Requirement[];
  findings: Finding[];
  repairs: Repair[];
  // --- extensions ---
  requirementCount: number;
  certificationCount: number;
  graphPaths: GraphPath[];
  runId: string | null;
  runStatus: RunStatus;
  runError: string | null;
  pipelineVersion: string | null;
  corpusVersion: string | null;
  corpusSource: string | null;
  warnings: string[];
  readinessFormula: string | null;
  isSample: boolean;
  persisted: boolean;
};

/** View model used by components: identical to the wire format except for a display date. */
export type ProcurementDocument = DocumentAnalysis;

export type DocumentSummary = Omit<
  DocumentAnalysis,
  "requirements" | "findings" | "repairs" | "graphPaths"
>;

export type StandardSummary = {
  id: string;
  number: string;
  title: string;
  category: string;
  status: string;
  related: string[];
  certification: "High" | "Medium" | "Low";
  // --- extensions ---
  verified?: boolean;
};

export type Clause = { id: string; text: string; section: string };

export type Standard = {
  id: string;
  number: string;
  title: string;
  scope: string;
  category: string;
  language: string;
  year: number;
  clauses: Clause[];
  relatedStandardIds: string[];
  certificationBodies: string[];
  // --- extensions ---
  status?: string;
  relationships?: Array<{
    id: string;
    type: string;
    direction: "out" | "in";
    standardId: string;
    number: string;
    note: string;
    confidence: number;
    method: string;
  }>;
  events?: Array<{ date: string | null; kind: string; summary: string }>;
  sourceNote?: string;
  verified?: boolean;
};

export type SearchResult = {
  standard: Standard;
  matchedClause: Clause;
  confidenceScore: number;
  explanation: string;
  // --- extensions ---
  provenance?: Provenance;
};

export type ChangeEvent = {
  id: string;
  date: string;
  standard: string;
  standardId: string;
  change: string;
  summary: string;
  severity: Severity;
  affected: Array<{ name: string; documentId: string | null }>;
};

export type WorkspaceStats = {
  documents: number;
  standardsMapped: number;
  requireAttention: number;
  averageReadiness: number | null;
};

/** Progress of an analysis run (GET /api/runs/{id}). `stage` is 1–8. */
export type RunState = {
  runId: string;
  documentId: string;
  status: RunStatus;
  stage: number;
  stageName: string | null;
  error: string | null;
  errorCode: string | null;
};

export type CorpusStatus = {
  version: string;
  source: "database" | "bundled-seed";
  clauses: number;
  relationships: number;
  events: number;
  standards: Array<{
    id: string;
    number: string;
    title: string;
    status: string;
    category: string;
    clauses: number;
    verified: boolean;
  }>;
};

export type AuditEntry = {
  id: string;
  at: string;
  actor: string | null;
  entityType: string;
  entityId: string;
  action: string;
  detail: string;
};
