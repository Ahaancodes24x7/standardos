import type { DocumentAnalysis, WorkspaceStats } from "./contracts";

// The DocumentAnalysis view model itself is built by the backend
// (backend/app/view.py); this module only aggregates it for the dashboard.

export function workspaceStats(
  documents: Array<Pick<DocumentAnalysis, "standards" | "status" | "readiness" | "runStatus">>,
): WorkspaceStats {
  const done = documents.filter((d) => d.runStatus === "succeeded");
  return {
    documents: done.length,
    standardsMapped: done.reduce((sum, d) => sum + d.standards, 0),
    requireAttention: done.filter((d) => d.status === "Review required").length,
    averageReadiness: done.length
      ? Math.round(done.reduce((sum, d) => sum + d.readiness, 0) / done.length)
      : null,
  };
}
