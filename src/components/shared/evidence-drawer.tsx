import { Link } from "@tanstack/react-router";
import { BookOpen, ExternalLink, ShieldCheck, Tag } from "lucide-react";
import type { Requirement } from "@/lib/contracts";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";

interface EvidenceDrawerProps {
  requirement: Requirement | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EvidenceDrawer({ requirement, open, onOpenChange }: EvidenceDrawerProps) {
  if (!requirement) return null;

  const confidencePct =
    requirement.confidence !== undefined ? Math.round(requirement.confidence * 100) : null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader className="border-b border-border/80 pb-4">
          <div className="flex items-center gap-2">
            <span className="grid size-6 place-items-center rounded-md bg-accent/30 text-accent-foreground">
              <BookOpen className="size-3.5" />
            </span>
            <p className="eyebrow">Requirement Inspector</p>
          </div>
          <SheetTitle className="mt-2 text-lg font-bold text-primary">{requirement.id}</SheetTitle>
          <SheetDescription className="text-xs">
            {requirement.category} {requirement.sectionLabel ? `· ${requirement.sectionLabel}` : ""}
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 pt-5">
          {/* Requirement Text */}
          <div className="rounded-xl border border-border/80 bg-background/80 p-4">
            <p className="text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground">
              Extracted Specification Text
            </p>
            <p className="mt-2 text-sm font-medium leading-relaxed text-primary">
              "{requirement.text}"
            </p>
          </div>

          {/* Governing Standard & Clause */}
          <div className="rounded-xl border border-border/80 bg-card p-4 space-y-3">
            <p className="text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground">
              Mapped Indian Standard
            </p>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-base font-bold text-accent-foreground">{requirement.standard}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Governing Clause: {requirement.clause || "General Provision"}
                </p>
              </div>
              {requirement.standardId && (
                <Button asChild size="sm" variant="outline" className="gap-1.5 shrink-0">
                  <Link to="/standard/$id" params={{ id: requirement.standardId }}>
                    <span>Standard</span>
                    <ExternalLink className="size-3" />
                  </Link>
                </Button>
              )}
            </div>

            {requirement.certification && (
              <div className="flex items-center gap-2 pt-2 border-t border-border/60 text-xs">
                <ShieldCheck className="size-4 text-accent-foreground" />
                <span className="font-semibold text-primary">Conformity Route:</span>
                <span className="text-muted-foreground">{requirement.certification}</span>
              </div>
            )}
          </div>

          {/* Intelligence & Confidence */}
          <div className="rounded-xl border border-border/80 bg-background/60 p-4 space-y-3">
            <p className="text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground">
              Evidence Basis
            </p>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Mapping Basis:</span>
              <span className="font-semibold capitalize text-primary">
                {requirement.basis?.replace(/_/g, " ") ?? "Standard citation"}
              </span>
            </div>
            {confidencePct !== null && (
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1.5">
                  <span className="text-muted-foreground">Model Confidence:</span>
                  <span className="text-primary">{confidencePct}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full bg-accent-foreground transition-all duration-300"
                    style={{ width: `${confidencePct}%` }}
                  />
                </div>
              </div>
            )}
            {requirement.explanation && (
              <p className="text-xs text-muted-foreground leading-relaxed pt-1">
                {requirement.explanation}
              </p>
            )}
          </div>

          {/* Provenance Trace */}
          {requirement.provenance && (
            <div className="rounded-xl border border-border/60 bg-muted/30 p-3 text-xs text-muted-foreground space-y-1">
              <div className="flex items-center gap-1.5 font-bold uppercase text-[10px] tracking-wider text-muted-foreground">
                <Tag className="size-3" />
                <span>Provenance Trace</span>
              </div>
              <p className="font-mono text-[11px] text-foreground">
                {requirement.provenance.component}@{requirement.provenance.componentVersion} ·{" "}
                {requirement.provenance.method}
              </p>
              {requirement.provenance.signals?.length > 0 && (
                <ul className="list-disc pl-4 space-y-0.5 pt-1 text-[11px]">
                  {requirement.provenance.signals.map((signal, idx) => (
                    <li key={idx}>{signal}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
