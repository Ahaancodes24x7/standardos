import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  AlertTriangle,
  Award,
  CheckCircle2,
  Clock3,
  FileWarning,
  Filter,
  Layers,
  Search,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { FindingsList } from "@/components/analysis/findings";
import { useReviewActions } from "@/components/analysis/use-review";
import type { FindingStatus, Severity } from "@/lib/contracts";
import { listDocuments } from "@/services/analysis";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { Input } from "@/components/ui/input";

export const Route = createFileRoute("/_authenticated/compliance")({
  loader: () => listDocuments(),
  head: () => ({
    meta: [
      { title: "Compliance Audit — STANDARDOS" },
      {
        name: "description",
        content: "Review verified, missing, conflicting, outdated, and certification findings.",
      },
      { property: "og:title", content: "Compliance Audit — STANDARDOS" },
      { property: "og:description", content: "Actionable procurement compliance findings." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Compliance,
});

const STATUS_CONFIG: Record<
  FindingStatus,
  { label: string; icon: typeof CheckCircle2; color: string; badge: string }
> = {
  conflicting: {
    label: "Conflicts",
    icon: AlertTriangle,
    color: "var(--destructive)",
    badge: "badge-crimson",
  },
  missing: {
    label: "Gaps / Missing",
    icon: FileWarning,
    color: "var(--warning-foreground)",
    badge: "badge-amber",
  },
  outdated: {
    label: "Outdated",
    icon: Clock3,
    color: "var(--warning)",
    badge: "badge-amber",
  },
  certification: {
    label: "Certification",
    icon: Award,
    color: "var(--accent-foreground)",
    badge: "badge-indigo",
  },
  verified: {
    label: "Verified",
    icon: CheckCircle2,
    color: "var(--success-foreground)",
    badge: "badge-emerald",
  },
};

function Compliance() {
  const documents = Route.useLoaderData();
  const { onReview } = useReviewActions(documents);
  const [activeStatus, setActiveStatus] = useState<FindingStatus | null>(null);

  const allFindings = useMemo(() => {
    return documents.flatMap((d) =>
      d.findings.map((f) => ({
        ...f,
        documentId: d.id,
        documentName: d.name,
      })),
    );
  }, [documents]);

  const conflicts = allFindings.filter((f) => f.status === "conflicting").length;
  const gaps = allFindings.filter((f) => f.status === "missing").length;
  const outdated = allFindings.filter((f) => f.status === "outdated").length;
  const certs = allFindings.filter((f) => f.status === "certification").length;
  const verified = allFindings.filter((f) => f.status === "verified").length;

  const displayedFindings = useMemo(() => {
    if (!activeStatus) return allFindings;
    return allFindings.filter((f) => f.status === activeStatus);
  }, [allFindings, activeStatus]);

  return (
    <div className="reveal space-y-8">
      {/* Header */}
      <PageHeader
        eyebrow="Workspace / Compliance Audit"
        title="Compliance Findings & Evidence"
        description="Every flag links the source requirement to governing Indian Standards, clause evidence, and recommended corrective action."
      />

      {/* Visual Hierarchy KPI Strip */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <button
          type="button"
          onClick={() => setActiveStatus(activeStatus === "conflicting" ? null : "conflicting")}
          className={`intel-card intel-card-hover p-4 text-left transition-all ${
            activeStatus === "conflicting" ? "ring-2 ring-destructive" : ""
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-destructive">
              Conflicts
            </span>
            <AlertTriangle className="size-4 text-destructive" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-primary">{conflicts}</div>
          <p className="mt-1 text-[11px] text-muted-foreground">Severe mismatch</p>
        </button>

        <button
          type="button"
          onClick={() => setActiveStatus(activeStatus === "missing" ? null : "missing")}
          className={`intel-card intel-card-hover p-4 text-left transition-all ${
            activeStatus === "missing" ? "ring-2 ring-warning" : ""
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-warning-foreground">
              Gaps
            </span>
            <FileWarning className="size-4 text-warning-foreground" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-primary">{gaps}</div>
          <p className="mt-1 text-[11px] text-muted-foreground">Missing clauses</p>
        </button>

        <button
          type="button"
          onClick={() => setActiveStatus(activeStatus === "outdated" ? null : "outdated")}
          className={`intel-card intel-card-hover p-4 text-left transition-all ${
            activeStatus === "outdated" ? "ring-2 ring-warning" : ""
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-warning-foreground">
              Outdated
            </span>
            <Clock3 className="size-4 text-warning-foreground" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-primary">{outdated}</div>
          <p className="mt-1 text-[11px] text-muted-foreground">Superseded editions</p>
        </button>

        <button
          type="button"
          onClick={() => setActiveStatus(activeStatus === "certification" ? null : "certification")}
          className={`intel-card intel-card-hover p-4 text-left transition-all ${
            activeStatus === "certification" ? "ring-2 ring-accent-foreground" : ""
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-accent-foreground">
              Certification
            </span>
            <Award className="size-4 text-accent-foreground" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-primary">{certs}</div>
          <p className="mt-1 text-[11px] text-muted-foreground">BIS conformity</p>
        </button>

        <button
          type="button"
          onClick={() => setActiveStatus(activeStatus === "verified" ? null : "verified")}
          className={`intel-card intel-card-hover p-4 text-left transition-all ${
            activeStatus === "verified" ? "ring-2 ring-success-foreground" : ""
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-success-foreground">
              Verified
            </span>
            <CheckCircle2 className="size-4 text-success-foreground" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-primary">{verified}</div>
          <p className="mt-1 text-[11px] text-muted-foreground">Normative match</p>
        </button>
      </section>

      {/* Main Filterable Findings List */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Displaying {displayedFindings.length} of {allFindings.length} Total Findings
            {activeStatus ? ` (Filtered by ${activeStatus})` : ""}
          </p>
          {activeStatus && (
            <button
              type="button"
              onClick={() => setActiveStatus(null)}
              className="text-xs font-bold text-accent-foreground hover:underline"
            >
              Clear filter
            </button>
          )}
        </div>

        <FindingsList findings={displayedFindings} onReview={onReview} />
      </section>
    </div>
  );
}
