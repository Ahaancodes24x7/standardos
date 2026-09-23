import { useState } from "react";
import { Award, BookOpenCheck, ClipboardCheck, FileText, FlaskConical } from "lucide-react";
import type { GraphPath, GraphPathNode } from "@/lib/contracts";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const ICONS: Record<GraphPathNode["kind"], typeof FileText> = {
  requirement: FileText,
  standard: BookOpenCheck,
  clause: ClipboardCheck,
  test: FlaskConical,
  certification: Award,
};
const EXPLAIN: Record<GraphPathNode["kind"], string> = {
  requirement: "The procurement requirement as extracted from the specification.",
  standard: "The standard this requirement was mapped to, by explicit citation or retrieval.",
  clause:
    "The clause that governs the requirement. Text shown is a paraphrased summary, not the normative wording.",
  test: "The test-method standard the governing standard relies on (TESTED_BY relationship in the standards graph).",
  certification: "The conformity route recorded for the governing standard.",
};

export function RelationshipGraph({ paths }: { paths: GraphPath[] }) {
  const [pathIndex, setPathIndex] = useState(0);
  const [active, setActive] = useState<string | null>(null);
  const path = paths[pathIndex];
  if (!path)
    return (
      <p className="py-10 text-center text-sm text-muted-foreground">
        No requirement could be mapped to a standard with enough confidence to draw a path.
      </p>
    );
  const nodes = path.nodes;
  const selected = nodes.find((node) => node.id === active);
  return (
    <>
      {paths.length > 1 && (
        <label className="flex flex-wrap items-center gap-3 text-sm font-semibold text-primary">
          Requirement
          <select
            className="min-w-0 max-w-full flex-1 rounded-sm border border-input bg-background/70 px-3 py-2 text-sm font-normal"
            value={pathIndex}
            onChange={(e) => {
              setPathIndex(Number(e.target.value));
              setActive(null);
            }}
          >
            {paths.map((p, i) => (
              <option key={p.requirementId} value={i}>
                {p.requirement.length > 110 ? `${p.requirement.slice(0, 107)}…` : p.requirement}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="overflow-x-auto pb-2">
        <div className="flex min-w-[760px] items-center py-10">
          {nodes.map((node, index) => {
            const Icon = ICONS[node.kind];
            const lit =
              !active ||
              active === node.id ||
              Math.abs(nodes.findIndex((item) => item.id === active) - index) === 1;
            return (
              <div key={node.id} className="contents">
                <button
                  type="button"
                  onMouseEnter={() => setActive(node.id)}
                  onMouseLeave={() => setActive(null)}
                  onFocus={() => setActive(node.id)}
                  onBlur={() => setActive(null)}
                  onClick={() => setActive(node.id)}
                  className={`glass-panel float-panel group grid w-32 shrink-0 place-items-center gap-3 p-4 text-center transition-opacity ${lit ? "opacity-100" : "opacity-35"}`}
                >
                  <span className="grid size-10 place-items-center rounded-full bg-accent text-accent-foreground group-hover:shadow-[0_0_24px_color-mix(in_oklab,var(--accent-foreground)_30%,transparent)]">
                    <Icon className="size-5" />
                  </span>
                  <span className="text-xs font-bold text-primary">{node.label}</span>
                </button>
                {index < nodes.length - 1 && (
                  <div
                    className={`graph-line h-px min-w-10 flex-1 transition-opacity ${lit ? "opacity-100" : "opacity-20"}`}
                  >
                    <span className="block h-1.5 w-1.5 -translate-y-[3px] rounded-full bg-accent-foreground" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      <p className="text-xs text-muted-foreground">
        Mapping confidence {Math.round(path.confidence * 100)}%.
      </p>
      <Dialog open={Boolean(active && selected)} onOpenChange={(open) => !open && setActive(null)}>
        {selected && (
          <DialogContent className="glass-panel">
            <DialogHeader>
              <DialogTitle>{selected.label}</DialogTitle>
              <DialogDescription>{selected.detail}</DialogDescription>
            </DialogHeader>
            <p className="text-sm leading-6 text-muted-foreground">{EXPLAIN[selected.kind]}</p>
          </DialogContent>
        )}
      </Dialog>
    </>
  );
}
