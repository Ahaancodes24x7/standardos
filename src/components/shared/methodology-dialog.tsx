import { useState } from "react";
import { Info, ShieldCheck, CheckCircle2, GitBranch, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface MethodologyDialogProps {
  title?: string | undefined;
  triggerText?: string | undefined;
  variant?: "outline" | "ghost" | "link" | undefined;
  size?: "sm" | "default" | undefined;
  children?: React.ReactNode | undefined;
}

export function MethodologyDialog({
  title = "StandardOS Intelligence Methodology",
  triggerText = "Methodology",
  variant = "outline",
  size = "sm",
  children,
}: MethodologyDialogProps) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant={variant} size={size} className="gap-1.5 text-xs font-semibold">
          <Info className="size-3.5 text-accent-foreground" />
          <span>{triggerText}</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <span className="grid size-7 place-items-center rounded-md bg-accent/30 text-accent-foreground">
              <ShieldCheck className="size-4" />
            </span>
            <p className="eyebrow">Evidence & Governance</p>
          </div>
          <DialogTitle className="mt-2 text-xl font-bold text-primary">{title}</DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Versioned, append-only evaluation and deterministic standards reasoning
          </DialogDescription>
        </DialogHeader>

        {children ?? (
          <div className="space-y-4 pt-2 text-sm text-foreground">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-border/80 bg-background/60 p-3.5">
                <div className="flex items-center gap-2 font-semibold text-primary">
                  <CheckCircle2 className="size-4 text-success-foreground" />
                  <span>95% Confidence Intervals</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Scores calculated via 1,000-sample bootstrap validation against curated gold
                  datasets.
                </p>
              </div>

              <div className="rounded-lg border border-border/80 bg-background/60 p-3.5">
                <div className="flex items-center gap-2 font-semibold text-primary">
                  <GitBranch className="size-4 text-accent-foreground" />
                  <span>Normative DAG Reasoning</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Transitive dependency traversal contracting superseded editions into verified
                  replacements.
                </p>
              </div>
            </div>

            <div className="rounded-lg border border-border/70 bg-muted/40 p-4 text-xs leading-relaxed text-muted-foreground">
              <p className="font-semibold text-primary">Blind Splits & Integrity Protection</p>
              <p className="mt-1">
                Development strictly isolates training/dev splits from blind benchmarks. Every
                evaluation run is appended to an immutable, versioned audit trail with git-backed
                commit hashes.
              </p>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
