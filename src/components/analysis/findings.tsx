import { useMemo, useState } from "react";
import {
  AlertTriangle,
  Award,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock3,
  ExternalLink,
  FileText,
  FileWarning,
  GitBranch,
  Layers,
  Search,
  ShieldCheck,
  Tag,
} from "lucide-react";
import type { Finding, FindingStatus, ReviewStatus, Severity } from "@/lib/contracts";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/shared/status-badge";

type OnReview = (finding: Finding, status: ReviewStatus, note: string) => Promise<void>;

interface FindingsListProps {
  findings: Finding[];
  onReview?: OnReview;
  showFilters?: boolean;
}

export function FindingsList({ findings, onReview, showFilters = true }: FindingsListProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      const matchStatus = statusFilter === "all" || f.status === statusFilter;
      const matchSeverity = severityFilter === "all" || f.severity === severityFilter;
      const matchQuery =
        !searchQuery.trim() ||
        (f.title + f.requirement + f.standard + f.reason)
          .toLowerCase()
          .includes(searchQuery.toLowerCase());
      return matchStatus && matchSeverity && matchQuery;
    });
  }, [findings, statusFilter, severityFilter, searchQuery]);

  const selected = findings.find((f) => f.id === selectedId) ?? null;

  return (
    <div className="space-y-4">
      {/* Filtering Toolbar */}
      {showFilters && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/70 bg-card/60 p-3">
          {/* Status Pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <button
              type="button"
              onClick={() => setStatusFilter("all")}
              className={`rounded-lg px-2.5 py-1 font-semibold transition ${
                statusFilter === "all"
                  ? "bg-primary text-primary-foreground font-bold shadow-xs"
                  : "text-muted-foreground hover:bg-muted hover:text-primary"
              }`}
            >
              All ({findings.length})
            </button>
            {(["conflicting", "missing", "outdated", "certification", "verified"] as const).map(
              (status) => {
                const count = findings.filter((f) => f.status === status).length;
                if (count === 0) return null;
                const active = statusFilter === status;
                return (
                  <button
                    key={status}
                    type="button"
                    onClick={() => setStatusFilter(active ? "all" : status)}
                    className={`rounded-lg px-2.5 py-1 text-xs font-semibold capitalize transition ${
                      active
                        ? "bg-primary text-primary-foreground font-bold shadow-xs"
                        : "text-muted-foreground hover:bg-muted hover:text-primary"
                    }`}
                  >
                    {status === "missing" ? "Gaps" : status} ({count})
                  </button>
                );
              },
            )}
          </div>

          {/* Search Box */}
          <div className="relative min-w-[200px] flex-1 sm:max-w-xs">
            <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search findings & standards..."
              className="h-8 pl-8 text-xs bg-background"
            />
          </div>
        </div>
      )}

      {/* Findings Cards List */}
      {!filteredFindings.length ? (
        <div className="intel-card py-12 text-center text-sm text-muted-foreground">
          {findings.length === 0
            ? "No compliance findings flagged."
            : "No findings match your filters."}
        </div>
      ) : (
        <div className="grid gap-3">
          {filteredFindings.map((finding) => (
            <div
              key={finding.id}
              onClick={() => setSelectedId(finding.id)}
              className={`intel-card intel-card-hover group cursor-pointer p-4 sm:p-5 transition-all ${
                finding.reviewStatus === "dismissed"
                  ? "opacity-55"
                  : finding.reviewStatus === "confirmed"
                    ? "border-success/40 bg-success/5"
                    : ""
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-2.5">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={finding.status} type="finding" size="sm" />
                  <StatusBadge status={finding.severity} type="severity" size="sm" />
                  <span className="font-mono text-xs font-bold text-accent-foreground">
                    {finding.standard}
                  </span>
                  {finding.documentName && (
                    <span className="text-[11px] text-muted-foreground">
                      · {finding.documentName}
                    </span>
                  )}
                </div>

                {finding.reviewStatus && (
                  <StatusBadge status={finding.reviewStatus} type="review" size="sm" />
                )}
              </div>

              {/* Title & Preview */}
              <div className="mt-3 flex items-start justify-between gap-4">
                <div className="space-y-1 min-w-0">
                  <h3 className="text-sm font-bold text-primary group-hover:text-accent-foreground transition">
                    {finding.title}
                  </h3>
                  <p className="line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                    {finding.reason}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="shrink-0 gap-1 text-xs text-muted-foreground group-hover:text-primary"
                >
                  <span>Inspect</span>
                  <ChevronRight className="size-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Deep Finding Detail Dialog */}
      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelectedId(null)}>
        {selected && <FindingDetail finding={selected} onReview={onReview} />}
      </Dialog>
    </div>
  );
}

function FindingDetail({
  finding,
  onReview,
}: {
  finding: Finding;
  onReview?: OnReview | undefined;
}) {
  const [note, setNote] = useState(finding.reviewNote ?? "");
  const [busy, setBusy] = useState(false);

  const review = async (status: ReviewStatus) => {
    if (!onReview) return;
    setBusy(true);
    try {
      await onReview(finding, status, note.trim());
    } finally {
      setBusy(false);
    }
  };

  // Find standard excerpt vs requirement excerpt if evidence available
  const standardEvidence = finding.evidence?.find(
    (e) => e.kind === "standard_clause" || e.standardId,
  );
  const requirementEvidence = finding.evidence?.find(
    (e) => e.kind === "requirement_text" || e.requirementId,
  );

  return (
    <DialogContent className="max-h-[92vh] max-w-3xl overflow-y-auto p-6 space-y-6">
      <DialogHeader className="border-b border-border/70 pb-4">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={finding.status} type="finding" size="md" />
          <StatusBadge status={finding.severity} type="severity" size="md" />
          {finding.reviewStatus && (
            <StatusBadge status={finding.reviewStatus} type="review" size="md" />
          )}
        </div>
        <DialogTitle className="mt-2 text-xl font-extrabold text-primary">
          {finding.title}
        </DialogTitle>
        <DialogDescription className="font-mono text-xs text-accent-foreground font-semibold">
          Governed by {finding.standard} {finding.rule ? `· Rule: ${finding.rule}` : ""}
        </DialogDescription>
      </DialogHeader>

      {/* Visual Contrast: Requirement VS Referenced Clause */}
      <div className="space-y-3">
        <p className="eyebrow">Evidence Comparison</p>
        <div className="grid gap-3 sm:grid-cols-2">
          {/* Requirement Side */}
          <div className="rounded-xl border border-border/80 bg-background/80 p-4 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <FileText className="size-3 text-accent-foreground" />
              <span>Specification Requirement</span>
            </span>
            <p className="text-xs font-semibold leading-relaxed text-primary">
              "{finding.requirement}"
            </p>
            {requirementEvidence && (
              <p className="text-[11px] text-muted-foreground border-t border-border/60 pt-1.5">
                {requirementEvidence.excerpt}
              </p>
            )}
          </div>

          {/* Governing Clause Side */}
          <div className="rounded-xl border border-accent/40 bg-accent/10 p-4 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-accent-foreground font-semibold flex items-center gap-1.5">
              <ShieldCheck className="size-3 text-accent-foreground" />
              <span>Governing Clause in {finding.standard}</span>
            </span>
            <p className="text-xs font-semibold leading-relaxed text-primary">{finding.reason}</p>
            {standardEvidence && (
              <p className="text-[11px] text-muted-foreground border-t border-accent/20 pt-1.5">
                {standardEvidence.excerpt}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Why This Was Detected Trail */}
      <div className="rounded-xl border border-border/80 bg-card p-4 space-y-2">
        <p className="eyebrow flex items-center gap-1.5">
          <GitBranch className="size-3.5 text-accent-foreground" />
          <span>Why This Was Detected</span>
        </p>
        <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-primary pt-1">
          <span className="rounded bg-muted px-2 py-1">Extracted Requirement</span>
          <span className="text-muted-foreground font-bold">➔</span>
          <span className="rounded bg-muted px-2 py-1">Normative Clause</span>
          <span className="text-muted-foreground font-bold">➔</span>
          <span className="rounded bg-accent/30 font-bold text-accent-foreground px-2 py-1">
            {finding.standard}
          </span>
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed pt-1">{finding.reason}</p>
      </div>

      {/* Recommended Action */}
      <div className="rounded-xl border border-border/80 bg-background/60 p-4 space-y-1.5">
        <p className="text-xs font-bold uppercase tracking-wider text-accent-foreground">
          Recommended Action
        </p>
        <p className="text-xs font-medium leading-relaxed text-primary">{finding.action}</p>
      </div>

      {/* Provenance Signals */}
      {finding.provenance && (
        <details className="rounded-lg border border-border/60 bg-muted/30 p-3 text-xs text-muted-foreground">
          <summary className="cursor-pointer font-bold uppercase tracking-wider text-[10px] text-muted-foreground">
            Provenance · {finding.provenance.component}@{finding.provenance.componentVersion} ·
            Confidence: {finding.provenance.confidence}
          </summary>
          <ul className="mt-2 list-disc pl-4 space-y-1 text-[11px]">
            {finding.provenance.signals?.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </details>
      )}

      {/* Reviewer Judgement Decision Form */}
      {onReview && (
        <div className="rounded-xl border border-border/80 bg-card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold uppercase tracking-wider text-primary">
              Reviewer Decision
            </p>
            <span className="text-[10px] text-muted-foreground">
              Recorded in immutable compliance audit trail
            </span>
          </div>

          <Textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Add reviewer notes or compliance sign-off rationale..."
            className="min-h-16 text-xs"
            maxLength={2000}
          />

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Button
              size="sm"
              disabled={busy}
              onClick={() => review("confirmed")}
              className="gap-1.5 bg-success text-success-foreground hover:bg-success/90"
            >
              <CheckCircle2 className="size-3.5 stroke-[3]" />
              <span>Confirm Finding</span>
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() => review("dismissed")}
              className="gap-1.5 text-xs text-muted-foreground hover:text-primary"
            >
              <span>Dismiss as Not Applicable</span>
            </Button>
            {finding.reviewStatus && finding.reviewStatus !== "open" && (
              <Button
                size="sm"
                variant="ghost"
                disabled={busy}
                onClick={() => review("open")}
                className="text-xs text-muted-foreground"
              >
                Reopen
              </Button>
            )}
          </div>
        </div>
      )}
    </DialogContent>
  );
}
