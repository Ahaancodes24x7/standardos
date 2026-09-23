import { useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, FileWarning, ShieldCheck } from "lucide-react";
import type { Finding, FindingStatus, ReviewStatus } from "@/lib/contracts";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const config: Record<
  FindingStatus,
  { label: string; icon: typeof CheckCircle2; className: string }
> = {
  verified: { label: "Verified", icon: CheckCircle2, className: "text-success-foreground" },
  missing: { label: "Missing", icon: FileWarning, className: "text-warning-foreground" },
  conflicting: { label: "Conflicting", icon: AlertTriangle, className: "text-destructive" },
  outdated: { label: "Outdated", icon: Clock3, className: "text-warning-foreground" },
  certification: { label: "Certification", icon: ShieldCheck, className: "text-accent-foreground" },
};

type OnReview = (finding: Finding, status: ReviewStatus, note: string) => Promise<void>;

export function FindingsList({ findings, onReview }: { findings: Finding[]; onReview?: OnReview }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = findings.find((f) => f.id === selectedId) ?? null;
  if (!findings.length)
    return (
      <p className="border-t border-border py-10 text-center text-sm text-muted-foreground">
        No findings.
      </p>
    );
  return (
    <>
      <div className="border-t border-border">
        {findings.map((finding) => {
          const item = config[finding.status];
          const Icon = item.icon;
          return (
            <button
              key={finding.id}
              type="button"
              onClick={() => setSelectedId(finding.id)}
              className={`thin-row grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-4 py-5 text-left ${finding.reviewStatus === "dismissed" ? "opacity-50" : ""}`}
            >
              <Icon className={`size-5 ${item.className}`} />
              <div className="min-w-0">
                <p className="font-bold text-primary">{finding.title}</p>
                <p className="mt-1 truncate text-sm text-muted-foreground">
                  {finding.documentName ? `${finding.documentName} · ` : ""}
                  {finding.standard}
                </p>
              </div>
              <span className={`text-xs font-bold uppercase ${item.className}`}>
                {finding.reviewStatus && finding.reviewStatus !== "open"
                  ? finding.reviewStatus
                  : finding.severity}
              </span>
            </button>
          );
        })}
      </div>
      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelectedId(null)}>
        {selected && <FindingDetail finding={selected} onReview={onReview} />}
      </Dialog>
    </>
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
  return (
    <DialogContent className="glass-panel max-h-[90vh] max-w-2xl overflow-y-auto">
      <DialogHeader>
        <p className="eyebrow">
          {config[finding.status].label} · {finding.severity} severity
          {finding.reviewStatus && finding.reviewStatus !== "open"
            ? ` · ${finding.reviewStatus} by reviewer`
            : ""}
        </p>
        <DialogTitle className="font-display text-3xl text-primary">{finding.title}</DialogTitle>
        <DialogDescription>{finding.standard}</DialogDescription>
      </DialogHeader>
      <dl className="mt-2 grid gap-5">
        <Detail label="Source requirement" value={finding.requirement} />
        <Detail label="Reason for flag" value={finding.reason} />
        <Detail label="Recommended action" value={finding.action} />
      </dl>
      {finding.evidence?.length ? (
        <section className="mt-2">
          <p className="text-xs font-bold uppercase tracking-[.08em] text-muted-foreground">
            Evidence
          </p>
          <ol className="mt-3 grid gap-3">
            {finding.evidence.map((e, i) => (
              <li key={i} className="border-l-2 border-accent pl-4 text-sm">
                <p className="font-semibold text-primary">
                  <span className="mr-2 text-[10px] font-bold uppercase tracking-[.08em] text-muted-foreground">
                    {e.kind.replace(/_/g, " ")}
                  </span>
                  {e.label}
                </p>
                <p className="mt-1 leading-6 text-muted-foreground">{e.excerpt}</p>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
      {finding.provenance && (
        <details className="mt-2 text-xs text-muted-foreground">
          <summary className="cursor-pointer font-bold uppercase tracking-[.08em]">
            Provenance · {finding.provenance.component}@{finding.provenance.componentVersion} ·{" "}
            {finding.provenance.method}
            {finding.provenance.model ? ` (${finding.provenance.model})` : ""} · confidence{" "}
            {finding.provenance.confidence}
          </summary>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {finding.provenance.signals.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </details>
      )}
      {onReview && (
        <section className="mt-2 border-t border-border pt-4">
          <p className="text-xs font-bold uppercase tracking-[.08em] text-muted-foreground">
            Reviewer decision
          </p>
          <Textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Optional note recorded in the audit trail…"
            className="mt-2 min-h-16"
            maxLength={2000}
          />
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" disabled={busy} onClick={() => review("confirmed")}>
              Confirm finding
            </Button>
            <Button size="sm" variant="outline" disabled={busy} onClick={() => review("dismissed")}>
              Dismiss as not applicable
            </Button>
            {finding.reviewStatus && finding.reviewStatus !== "open" && (
              <Button size="sm" variant="ghost" disabled={busy} onClick={() => review("open")}>
                Reopen
              </Button>
            )}
          </div>
        </section>
      )}
    </DialogContent>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-l-2 border-accent-foreground pl-4">
      <dt className="text-xs font-bold uppercase tracking-[.08em] text-muted-foreground">
        {label}
      </dt>
      <dd className="mt-2 text-sm leading-6 text-primary">{value}</dd>
    </div>
  );
}
