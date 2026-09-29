import type {
  ChangeEvent,
  CorpusStatus,
  DocumentAnalysis,
  Finding,
  FindingStatus,
  Severity,
} from "@/lib/contracts";

// Workspace aggregates for the dashboard. Everything is derived from the analyses the
// API returns (documents with requirements and findings), the standards corpus status
// and the change-impact feed — nothing here is estimated or invented.

export const IST = "Asia/Kolkata";

/** Indian digit grouping: 1,23,456. */
export const inr = (n: number) => n.toLocaleString("en-IN");

export function istDate(iso: string | Date, opts: Intl.DateTimeFormatOptions = {}) {
  const d = typeof iso === "string" ? new Date(iso) : iso;
  return new Intl.DateTimeFormat("en-IN", { timeZone: IST, ...opts }).format(d);
}

/** Calendar day in IST as YYYY-MM-DD (for bucketing). */
export function istDay(iso: string | Date) {
  const d = typeof iso === "string" ? new Date(iso) : iso;
  return new Intl.DateTimeFormat("en-CA", { timeZone: IST }).format(d);
}

export function istGreeting(now = new Date()) {
  const hour = Number(
    new Intl.DateTimeFormat("en-IN", { timeZone: IST, hour: "numeric", hour12: false }).format(now),
  );
  return hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
}

export const STATUS_META: Record<FindingStatus, { label: string; color: string }> = {
  conflicting: { label: "Conflicts", color: "var(--chart-conflict)" },
  missing: { label: "Gaps", color: "var(--chart-gap)" },
  outdated: { label: "Outdated IS", color: "var(--chart-outdated)" },
  certification: { label: "BIS / certification", color: "var(--chart-cert)" },
  verified: { label: "Verified", color: "var(--chart-verified)" },
};

const SEVERITY_RANK: Record<Severity, number> = { high: 0, medium: 1, low: 2 };

export type StandardUse = {
  id: string;
  label: string;
  title: string;
  status: string;
  category: string;
  requirements: number;
  documents: number;
  openFindings: number;
};

export type NetworkEdge = {
  doc: string;
  standard: string;
  weight: number;
  tone: "ok" | "gap" | "conflict";
};

export type PriorityItem = Finding & { documentId: string; documentName: string };

export type Insights = {
  analysed: DocumentAnalysis[];
  processing: number;
  failed: number;
  requirements: number;
  standardsReferenced: number;
  openFindings: number;
  highSeverity: number;
  averageReadiness: number | null;
  readinessBands: Array<{
    key: string;
    label: string;
    range: string;
    count: number;
    color: string;
  }>;
  statusCounts: Array<{ status: FindingStatus; label: string; count: number; color: string }>;
  categories: Array<{ name: string; count: number }>;
  standards: StandardUse[];
  domains: Array<{ name: string; requirements: number; standards: number }>;
  priority: PriorityItem[];
  certification: PriorityItem[];
  outdatedReferences: PriorityItem[];
  activity: Array<{ day: string; label: string; analyses: number }>;
  documentTypes: Array<{ name: string; count: number }>;
  organisations: Array<{ name: string; documents: number; avgReadiness: number }>;
  network: { documents: DocumentAnalysis[]; standards: StandardUse[]; edges: NetworkEdge[] };
  alerts: ChangeEvent[];
};

const isOpen = (f: Finding) => f.status !== "verified" && f.reviewStatus !== "dismissed";

function findingStandardId(f: Finding): string | null {
  return f.evidence?.find((e) => e.standardId)?.standardId ?? null;
}

function countBy<T>(items: T[], key: (item: T) => string) {
  const map = new Map<string, number>();
  for (const item of items) map.set(key(item), (map.get(key(item)) ?? 0) + 1);
  return [...map.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
}

export function buildInsights(
  documents: DocumentAnalysis[],
  corpus: CorpusStatus | null,
  events: ChangeEvent[],
  now = new Date(),
): Insights {
  const analysed = documents.filter((d) => d.runStatus === "succeeded");
  const corpusById = new Map((corpus?.standards ?? []).map((s) => [s.id, s]));

  const allFindings = analysed.flatMap((d) =>
    (d.findings ?? []).map((f) => ({ ...f, documentId: d.id, documentName: d.name })),
  );
  const open = allFindings.filter(isOpen);

  // --- standards referenced by requirements -------------------------------------------
  const byStandard = new Map<string, StandardUse & { docs: Set<string> }>();
  for (const doc of analysed) {
    for (const req of doc.requirements ?? []) {
      if (!req.standardId) continue;
      const meta = corpusById.get(req.standardId);
      const entry =
        byStandard.get(req.standardId) ??
        ({
          id: req.standardId,
          label: meta?.number ?? req.standard,
          title: meta?.title ?? "",
          status: meta?.status ?? "Current",
          category: meta?.category ?? "Other",
          requirements: 0,
          documents: 0,
          openFindings: 0,
          docs: new Set<string>(),
        } satisfies StandardUse & { docs: Set<string> });
      entry.requirements += 1;
      entry.docs.add(doc.id);
      byStandard.set(req.standardId, entry);
    }
  }
  for (const f of open) {
    const id = findingStandardId(f);
    const entry = id ? byStandard.get(id) : undefined;
    if (entry) entry.openFindings += 1;
  }
  const standards: StandardUse[] = [...byStandard.values()]
    .map(({ docs, ...rest }) => ({ ...rest, documents: docs.size }))
    .sort((a, b) => b.requirements - a.requirements);

  const domainMap = new Map<string, { requirements: number; standards: number }>();
  for (const s of standards) {
    const d = domainMap.get(s.category) ?? { requirements: 0, standards: 0 };
    d.requirements += s.requirements;
    d.standards += 1;
    domainMap.set(s.category, d);
  }

  // --- readiness -------------------------------------------------------------------------
  const bands = [
    {
      key: "ready",
      label: "Bid-ready",
      range: "≥ 80%",
      min: 80,
      max: 101,
      color: "var(--chart-verified)",
    },
    {
      key: "review",
      label: "Needs review",
      range: "50–79%",
      min: 50,
      max: 80,
      color: "var(--chart-gap)",
    },
    {
      key: "risk",
      label: "At risk",
      range: "< 50%",
      min: -1,
      max: 50,
      color: "var(--chart-conflict)",
    },
  ];

  // --- activity: last 14 IST days --------------------------------------------------------
  const perDay = new Map<string, number>();
  for (const d of documents)
    perDay.set(istDay(d.analyzedAt), (perDay.get(istDay(d.analyzedAt)) ?? 0) + 1);
  const activity = Array.from({ length: 14 }, (_, i) => {
    const day = new Date(now.getTime() - (13 - i) * 86_400_000);
    const key = istDay(day);
    return {
      day: key,
      label: istDate(day, { day: "numeric", month: "short" }),
      analyses: perDay.get(key) ?? 0,
    };
  });

  // --- organisations (departments / buyers) ----------------------------------------------
  const orgMap = new Map<string, { documents: number; readiness: number }>();
  for (const d of analysed) {
    const o = orgMap.get(d.organization) ?? { documents: 0, readiness: 0 };
    o.documents += 1;
    o.readiness += d.readiness;
    orgMap.set(d.organization, o);
  }

  // --- specification ↔ standard network ---------------------------------------------------
  const netDocs = analysed.slice(0, 6);
  const netStandards = standards
    .filter((s) => netDocs.some((d) => d.requirements?.some((r) => r.standardId === s.id)))
    .slice(0, 8);
  const edges: NetworkEdge[] = [];
  for (const doc of netDocs) {
    const docOpen = (doc.findings ?? []).filter(isOpen);
    for (const s of netStandards) {
      const weight = (doc.requirements ?? []).filter((r) => r.standardId === s.id).length;
      if (!weight) continue;
      const onStd = docOpen.filter((f) => findingStandardId(f) === s.id);
      const tone = onStd.some((f) => f.status === "conflicting")
        ? "conflict"
        : onStd.length
          ? "gap"
          : "ok";
      edges.push({ doc: doc.id, standard: s.id, weight, tone });
    }
  }

  const bySeverity = (a: PriorityItem, b: PriorityItem) =>
    SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity];

  return {
    analysed,
    processing: documents.filter((d) => d.runStatus === "queued" || d.runStatus === "running")
      .length,
    failed: documents.filter((d) => d.runStatus === "failed").length,
    requirements: analysed.reduce(
      (sum, d) => sum + (d.requirementCount ?? d.requirements?.length ?? 0),
      0,
    ),
    standardsReferenced: standards.length,
    openFindings: open.length,
    highSeverity: open.filter((f) => f.severity === "high").length,
    averageReadiness: analysed.length
      ? Math.round(analysed.reduce((sum, d) => sum + d.readiness, 0) / analysed.length)
      : null,
    readinessBands: bands.map(({ min, max, ...b }) => ({
      ...b,
      count: analysed.filter((d) => d.readiness >= min && d.readiness < max).length,
    })),
    statusCounts: (Object.keys(STATUS_META) as FindingStatus[]).map((status) => ({
      status,
      label: STATUS_META[status].label,
      color: STATUS_META[status].color,
      count: allFindings.filter((f) => f.status === status && (status === "verified" || isOpen(f)))
        .length,
    })),
    categories: countBy(
      analysed.flatMap((d) => d.requirements ?? []),
      (r) => r.category || "general",
    ),
    standards,
    domains: [...domainMap.entries()]
      .map(([name, v]) => ({ name, ...v }))
      .sort((a, b) => b.requirements - a.requirements),
    priority: [...open].sort(bySeverity).slice(0, 6),
    certification: open.filter((f) => f.status === "certification"),
    outdatedReferences: open.filter((f) => f.status === "outdated"),
    activity,
    documentTypes: countBy(documents, (d) => d.documentTypeLabel || "Technical specification"),
    organisations: [...orgMap.entries()]
      .map(([name, o]) => ({
        name,
        documents: o.documents,
        avgReadiness: Math.round(o.readiness / o.documents),
      }))
      .sort((a, b) => b.documents - a.documents)
      .slice(0, 5),
    network: { documents: netDocs, standards: netStandards, edges },
    alerts: [...events]
      .sort(
        (a, b) =>
          Number(b.affected.length > 0) - Number(a.affected.length > 0) ||
          SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity],
      )
      .slice(0, 5),
  };
}
