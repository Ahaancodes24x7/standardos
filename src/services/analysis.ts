import { hasDemoSession } from "@/contexts/auth-context";
import { api, ApiError } from "@/lib/api";
import type {
  AuditEntry,
  ChangeEvent,
  ClassifierComparison,
  CorpusStatus,
  DependencyDag,
  DocumentAnalysis,
  EngineInfo,
  EvaluationRun,
  ProcurementDocument,
  RepairStatus,
  ReviewStatus,
  RunState,
  SearchResult,
  Standard,
  StandardDependencies,
  StandardSummary,
} from "@/lib/contracts";
import { buildComplianceReport } from "@/lib/report";

// Frontend service layer. Pages call these functions only; each one talks to
// the FastAPI backend, or — for the account-less demo workspace — to its
// stateless endpoints, keeping demo results in sessionStorage.

export type AnalysisInput = { file?: File | undefined; text?: string | undefined };

const LOCAL_KEY = "standardos-local-analyses";

function readLocal(): Record<string, DocumentAnalysis> {
  try {
    return JSON.parse(window.sessionStorage.getItem(LOCAL_KEY) ?? "{}") as Record<
      string,
      DocumentAnalysis
    >;
  } catch {
    return {};
  }
}

function writeLocal(doc: DocumentAnalysis) {
  try {
    window.sessionStorage.setItem(LOCAL_KEY, JSON.stringify({ ...readLocal(), [doc.id]: doc }));
  } catch {
    // Storage full or unavailable: the result is still shown for this navigation.
  }
}

function toFormData(input: AnalysisInput) {
  const form = new FormData();
  if (input.file) form.append("file", input.file);
  if (input.text?.trim()) form.append("text", input.text);
  return form;
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const POLL_MS = 400;
const TIMEOUT_MS = 5 * 60 * 1000;

const getRun = (runId: string) => api.get<RunState>(`/api/runs/${runId}`);

/** Poll a run until it finishes; `onProgress` receives the 1-based pipeline stage (1–8). */
async function waitForRun(runId: string, onProgress?: (step: number) => void): Promise<RunState> {
  const deadline = Date.now() + TIMEOUT_MS;
  for (;;) {
    let run: RunState | null = null;
    try {
      run = await getRun(runId);
    } catch {
      // Transient polling errors are ignored until the deadline.
    }
    if (run?.stage) onProgress?.(run.stage);
    if (run && (run.status === "succeeded" || run.status === "failed")) return run;
    if (Date.now() > deadline)
      throw new Error("The analysis is taking longer than expected. Check Documents later.");
    await sleep(POLL_MS);
  }
}

/**
 * Upload and analyse a specification. The backend stores the document, queues
 * a run and executes it in the background while this polls stage progress.
 */
export async function analyzeDocument(
  input: AnalysisInput,
  onProgress?: (step: number) => void,
): Promise<{ id: string }> {
  if (!input.file && !input.text?.trim())
    throw new Error("Add a document or specification text first.");

  if (hasDemoSession()) {
    onProgress?.(1);
    const doc = await api.upload<DocumentAnalysis>("/api/analyze/stateless", toFormData(input));
    writeLocal(doc);
    onProgress?.(8);
    return { id: doc.id };
  }

  const { documentId, runId } = await api.upload<{ documentId: string; runId: string }>(
    "/api/analyses",
    toFormData(input),
  );
  onProgress?.(1);
  const run = await waitForRun(runId, onProgress);
  if (run.status === "failed") throw new Error(run.error ?? "The analysis failed.");
  onProgress?.(8);
  return { id: documentId };
}

const sampleWorkspace = () => api.get<DocumentAnalysis[]>("/api/samples");

export async function getAnalysis(id: string): Promise<ProcurementDocument | null> {
  if (hasDemoSession() || id.startsWith("local-") || id.startsWith("sample-")) {
    const local = readLocal()[id];
    if (local) return local;
    return (await sampleWorkspace()).find((d) => d.id === id) ?? null;
  }
  try {
    return await api.get<DocumentAnalysis>(`/api/documents/${id}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function listDocuments(): Promise<ProcurementDocument[]> {
  if (hasDemoSession()) return [...(await sampleWorkspace()), ...Object.values(readLocal())];
  return api.get<DocumentAnalysis[]>("/api/documents");
}

export async function reanalyze(documentId: string) {
  const { runId } = await api.post<{ runId: string }>(`/api/documents/${documentId}/reanalyze`);
  const run = await waitForRun(runId);
  if (run.status === "failed") throw new Error(run.error ?? "The analysis failed.");
}

export const getAuditTrail = (documentId: string) =>
  api.get<AuditEntry[]>(`/api/documents/${documentId}/audit`);

export async function getChangeImpact(): Promise<ChangeEvent[]> {
  return api.get<ChangeEvent[]>("/api/change-impact", {
    scope: hasDemoSession() ? "sample" : "workspace",
  });
}

/** Record a reviewer's judgement of a finding. Returns false when not persisted (demo). */
export async function reviewFinding(
  doc: Pick<DocumentAnalysis, "persisted">,
  findingId: string,
  status: ReviewStatus,
  note?: string,
): Promise<boolean> {
  if (!doc.persisted) return false;
  await api.post(`/api/findings/${findingId}/review`, { status, note: note ?? null });
  return true;
}

export async function decideRepair(
  doc: Pick<DocumentAnalysis, "persisted">,
  repairId: string,
  decision: RepairStatus,
  text?: string,
): Promise<boolean> {
  if (!doc.persisted) return false;
  await api.post(`/api/repairs/${repairId}/decision`, { decision, text: text ?? null });
  return true;
}

export async function downloadComplianceReport(doc: DocumentAnalysis) {
  const { filename, markdown } = doc.persisted
    ? await api.get<{ filename: string; markdown: string }>(`/api/documents/${doc.id}/report`)
    : {
        filename: `${doc.name.replace(/[^\w.-]+/g, "_").slice(0, 80)}-compliance-report.md`,
        markdown: buildComplianceReport(doc),
      };
  const url = URL.createObjectURL(new Blob([markdown], { type: "text/markdown;charset=utf-8" }));
  const link = Object.assign(document.createElement("a"), { href: url, download: filename });
  link.click();
  URL.revokeObjectURL(url);
}

export const listStandards = (): Promise<StandardSummary[]> => api.get("/api/standards");

export async function getStandard(id: string): Promise<Standard | null> {
  try {
    return await api.get<Standard>(`/api/standards/${encodeURIComponent(id)}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export const searchStandards = (
  query: string,
  filters: { domains?: string[]; yearRanges?: Array<"2020-" | "2010-2019" | "-2009"> } = {},
): Promise<SearchResult[]> => api.post("/api/standards/search", { query, ...filters });

export const getCorpusStatus = (): Promise<CorpusStatus> => api.get("/api/corpus/status");

export const getStandardDependencies = (id: string): Promise<StandardDependencies> =>
  api.get(`/api/standards/${encodeURIComponent(id)}/dependencies`);

export const getDependencyDag = (): Promise<DependencyDag> => api.get("/api/dependency-dag");

export const getEngineInfo = (): Promise<EngineInfo> => api.get("/api/engine");

export const listEvaluationRuns = (): Promise<EvaluationRun[]> => api.get("/api/evaluation/runs");

export async function getClassifierComparison(): Promise<ClassifierComparison | null> {
  try {
    return await api.get<ClassifierComparison>("/api/evaluation/classifiers");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

/** Replace the stored standards corpus with a JSON file (corpus administrators only). */
export function importCorpus(file: File) {
  const form = new FormData();
  form.append("file", file);
  return api.upload<{ version: string; standards: number; clauses: number; relationships: number }>(
    "/api/admin/corpus/import",
    form,
  );
}

/** "Today, 10:42" / "Yesterday, 16:18" / "18 Sep 2026" in the viewer's timezone. */
export function formatAnalyzedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const now = new Date();
  const time = date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  const sameDay = (a: Date, b: Date) => a.toDateString() === b.toDateString();
  if (sameDay(date, now)) return `Today, ${time}`;
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (sameDay(date, yesterday)) return `Yesterday, ${time}`;
  return date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}
