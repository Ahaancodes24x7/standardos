import { useState } from "react";
import {
  Award,
  BookOpenCheck,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  ExternalLink,
  FileText,
  FlaskConical,
  Info,
} from "lucide-react";
import type { GraphPath, GraphPathNode } from "@/lib/contracts";

const ICONS: Record<GraphPathNode["kind"], typeof FileText> = {
  requirement: FileText,
  standard: BookOpenCheck,
  clause: ClipboardCheck,
  test: FlaskConical,
  certification: Award,
};

const EXPLAIN: Record<GraphPathNode["kind"], string> = {
  requirement: "The procurement requirement extracted from the specification text.",
  standard:
    "The Indian Standard mapped to this requirement by explicit citation or semantic retrieval.",
  clause:
    "The governing clause in the standard. Text is an indexed summary for compliance reasoning.",
  test: "Normative test method standard required by the governing standard (TESTED_BY edge in DAG).",
  certification: "Mandatory conformity assessment or BIS certification route for this product.",
};

const KIND_LABEL: Record<GraphPathNode["kind"], string> = {
  requirement: "Requirement",
  standard: "Standard",
  clause: "Clause",
  test: "Test Method",
  certification: "Certification",
};

export function RelationshipGraph({ paths }: { paths: GraphPath[] }) {
  const [pathIndex, setPathIndex] = useState(0);
  const path = paths[pathIndex];
  const [activeNodeId, setActiveNodeId] = useState<string | null>(path?.nodes[0]?.id ?? null);

  if (!path) {
    return (
      <div className="intel-card py-12 text-center text-sm text-muted-foreground">
        No requirement could be mapped to a standard with sufficient confidence to draw an evidence
        path.
      </div>
    );
  }

  const nodes = path.nodes;
  const activeNode = nodes.find((n) => n.id === activeNodeId) ?? nodes[0];
  const confidencePct = Math.round(path.confidence * 100);

  return (
    <div className="space-y-6">
      {/* Path Selector Bar */}
      {paths.length > 1 && (
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-border/80 bg-card p-3.5">
          <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Select Requirement Path ({pathIndex + 1} of {paths.length})
          </label>
          <select
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold text-primary max-w-md truncate"
            value={pathIndex}
            onChange={(e) => {
              const idx = Number(e.target.value);
              setPathIndex(idx);
              setActiveNodeId(paths[idx]?.nodes[0]?.id ?? null);
            }}
          >
            {paths.map((p, i) => (
              <option key={p.requirementId} value={i}>
                {p.requirement.length > 90 ? `${p.requirement.slice(0, 87)}…` : p.requirement}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Interactive Path Canvas */}
      <div className="intel-card p-6 overflow-hidden">
        <div className="flex items-center justify-between border-b border-border/70 pb-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="font-bold text-primary">Evidence Trail</span>
            <span className="text-muted-foreground">·</span>
            <span className="text-muted-foreground">
              Click any node to inspect governing details
            </span>
          </div>
          <span className="rounded-full bg-accent/30 px-2.5 py-0.5 font-mono text-[11px] font-bold text-accent-foreground">
            Confidence {confidencePct}%
          </span>
        </div>

        {/* Node Sequence */}
        <div className="overflow-x-auto py-8 custom-scrollbar">
          <div className="flex min-w-[720px] items-center justify-between px-2">
            {nodes.map((node, index) => {
              const Icon = ICONS[node.kind];
              const isSelected = activeNode?.id === node.id;

              return (
                <div key={node.id} className="flex items-center flex-1 last:flex-none">
                  {/* Node Button */}
                  <button
                    type="button"
                    onClick={() => setActiveNodeId(node.id)}
                    className={`group relative flex flex-col items-center gap-2.5 rounded-xl border p-3 text-center transition-all ${
                      isSelected
                        ? "border-accent-foreground bg-accent/25 shadow-md ring-2 ring-accent-foreground/30 scale-105"
                        : "border-border/80 bg-background/80 hover:border-accent-foreground/60 hover:bg-card"
                    }`}
                    style={{ minWidth: "115px" }}
                  >
                    <span
                      className={`grid size-9 place-items-center rounded-lg transition-transform group-hover:scale-110 ${
                        isSelected
                          ? "bg-accent-foreground text-background"
                          : "bg-accent/40 text-accent-foreground"
                      }`}
                    >
                      <Icon className="size-4.5" />
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                      {KIND_LABEL[node.kind]}
                    </span>
                    <span className="max-w-[100px] truncate text-xs font-bold text-primary">
                      {node.label}
                    </span>
                  </button>

                  {/* Connecting Edge Arrow */}
                  {index < nodes.length - 1 && (
                    <div className="flex-1 flex items-center px-2">
                      <div className="h-0.5 w-full bg-linear-to-r from-accent-foreground/60 to-accent-foreground relative">
                        <span className="absolute right-0 top-1/2 -translate-y-1/2 size-1.5 rounded-full bg-accent-foreground" />
                      </div>
                      <ChevronRight className="size-4 text-accent-foreground -ml-1 shrink-0" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Node Inspector Pane */}
        {activeNode && (
          <div className="mt-4 rounded-xl border border-border/80 bg-card/90 p-5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="eyebrow flex items-center gap-1.5">
                <Info className="size-3.5" />
                <span>Node Details: {KIND_LABEL[activeNode.kind]}</span>
              </span>
              <span className="font-mono text-xs font-bold text-accent-foreground">
                {activeNode.label}
              </span>
            </div>
            <p className="text-sm font-semibold text-primary">{activeNode.detail}</p>
            <p className="text-xs text-muted-foreground leading-relaxed pt-1 border-t border-border/50">
              {EXPLAIN[activeNode.kind]}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
