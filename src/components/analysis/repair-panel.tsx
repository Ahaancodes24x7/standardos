import { useState } from "react";
import { Check, Edit3, RotateCcw, ShieldCheck, Tag, X } from "lucide-react";
import type { Repair, RepairStatus } from "@/lib/contracts";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type OnDecide = (repair: Repair, decision: RepairStatus, text?: string) => Promise<void>;

export function RepairPanel({ repairs, onDecide }: { repairs: Repair[]; onDecide?: OnDecide }) {
  const [states, setStates] = useState<Record<string, RepairStatus>>(() =>
    Object.fromEntries(repairs.map((r) => [r.id, r.status ?? "pending"])),
  );
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const decide = async (repair: Repair, decision: RepairStatus, text?: string) => {
    setBusy(repair.id);
    try {
      await onDecide?.(repair, decision, text);
      setStates((s) => ({ ...s, [repair.id]: decision }));
      if (decision !== "edited") setEdits(({ [repair.id]: _dropped, ...rest }) => rest);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      {repairs.map((repair, index) => {
        const state = states[repair.id] ?? "pending";
        const editing = edits[repair.id] !== undefined;
        const shown =
          state === "edited" && repair.finalText && !editing
            ? repair.finalText
            : repair.recommended;

        return (
          <article
            key={repair.id}
            className={`intel-card p-6 space-y-5 transition-all ${
              state === "accepted"
                ? "border-success/50 bg-success/5"
                : state === "rejected"
                  ? "border-destructive/30 bg-destructive/5 opacity-70"
                  : ""
            }`}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border/70 pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-accent-foreground">
                  CORRECTION #{String(index + 1).padStart(2, "0")}
                </span>
                <span className="text-muted-foreground">·</span>
                <span className="text-xs text-muted-foreground">Evidence-backed revision</span>
              </div>
              <span
                className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                  state === "accepted"
                    ? "bg-success/20 text-success-foreground"
                    : state === "rejected"
                      ? "bg-destructive/20 text-destructive"
                      : state === "edited"
                        ? "bg-accent/30 text-accent-foreground"
                        : "bg-muted text-muted-foreground"
                }`}
              >
                {state === "pending" ? "Pending Review" : state}
              </span>
            </div>

            {/* Side-by-side Diff */}
            <div className="grid gap-4 lg:grid-cols-2">
              {/* Original */}
              <div className="rounded-xl border border-border/70 bg-background/60 p-4 space-y-1.5">
                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  Original Specification Requirement
                </p>
                <p className="text-xs leading-relaxed text-muted-foreground line-through decoration-destructive/40">
                  {repair.original}
                </p>
              </div>

              {/* Recommended */}
              <div className="rounded-xl border border-accent/40 bg-accent/10 p-4 space-y-1.5">
                <p className="text-[10px] font-bold uppercase tracking-wider text-accent-foreground font-semibold">
                  StandardOS Recommended Correction
                </p>
                {editing ? (
                  <Textarea
                    value={edits[repair.id]}
                    onChange={(event) => setEdits({ ...edits, [repair.id]: event.target.value })}
                    className="min-h-24 text-xs font-mono"
                  />
                ) : (
                  <p className="text-xs leading-relaxed font-semibold text-primary">{shown}</p>
                )}
              </div>
            </div>

            {/* Evidence & Reason Strip */}
            <div className="grid gap-3 rounded-lg border border-border/60 bg-muted/20 p-3.5 text-xs sm:grid-cols-2">
              <div>
                <span className="font-bold text-primary">Governing Standard & Evidence:</span>
                <p className="mt-0.5 text-muted-foreground">{repair.evidence}</p>
              </div>
              <div>
                <span className="font-bold text-primary">Detection Reason:</span>
                <p className="mt-0.5 text-muted-foreground">{repair.reason}</p>
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="text-[11px] text-muted-foreground">
                {repair.provenance ? (
                  <span>
                    Generated via {repair.provenance.component} ({repair.provenance.method})
                  </span>
                ) : (
                  <span>Decision will be saved to immutable audit trail</span>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                {editing ? (
                  <>
                    <Button
                      size="sm"
                      disabled={busy === repair.id || !edits[repair.id]?.trim()}
                      onClick={() => decide(repair, "edited", edits[repair.id])}
                      className="gap-1.5"
                    >
                      <Check className="size-3.5" />
                      <span>Save Edited Text</span>
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setEdits(({ [repair.id]: _dropped, ...rest }) => rest)}
                    >
                      Cancel
                    </Button>
                  </>
                ) : state === "pending" ? (
                  <>
                    <Button
                      size="sm"
                      disabled={busy === repair.id}
                      onClick={() => decide(repair, "accepted")}
                      className="gap-1.5 bg-success text-success-foreground hover:bg-success/90"
                    >
                      <Check className="size-3.5 stroke-[3]" />
                      <span>Accept Change</span>
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={busy === repair.id}
                      onClick={() => decide(repair, "rejected")}
                      className="gap-1.5 text-destructive hover:bg-destructive/10"
                    >
                      <X className="size-3.5" />
                      <span>Reject</span>
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setEdits({ ...edits, [repair.id]: repair.recommended })}
                      className="gap-1.5"
                    >
                      <Edit3 className="size-3.5" />
                      <span>Edit Custom</span>
                    </Button>
                  </>
                ) : (
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={busy === repair.id}
                    onClick={() => decide(repair, "pending")}
                    className="gap-1.5 text-xs text-muted-foreground"
                  >
                    <RotateCcw className="size-3.5" />
                    <span>Undo Decision</span>
                  </Button>
                )}
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
