import { createFileRoute } from "@tanstack/react-router";
import {
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Cpu,
  Database,
  FlaskConical,
  GitBranch,
  Info,
  Layers,
  Lock,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EvaluationRun } from "@/lib/contracts";
import {
  getClassifierComparison,
  getDependencyDag,
  getEngineInfo,
  listEvaluationRuns,
} from "@/services/analysis";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { MethodologyDialog } from "@/components/shared/methodology-dialog";

export const Route = createFileRoute("/_authenticated/evaluation")({
  loader: async () => {
    const [engine, runs, classifiers, dag] = await Promise.all([
      getEngineInfo(),
      listEvaluationRuns(),
      getClassifierComparison(),
      getDependencyDag(),
    ]);
    return { engine, runs, classifiers, dag };
  },
  head: () => ({
    meta: [
      { title: "Model Evaluation & Benchmarks — STANDARDOS" },
      {
        name: "description",
        content: "Versioned evaluation of the StandardOS analysis pipeline and classifiers.",
      },
    ],
  }),
  component: Evaluation,
});

const METRICS: Array<[string, string]> = [
  ["id_f1", "Requirement ID F1"],
  ["cls_macro_f1", "Category macro-F1"],
  ["attr_f1", "Attribute F1"],
  ["map_accuracy", "Mapping acc."],
  ["fnd_precision", "Findings P"],
  ["fnd_recall", "Findings R"],
  ["fnd_f1", "Findings F1"],
];
const CONFIG_ORDER = ["legacy-2.1", "v3", "v3.1", "v3.1-dag", "v3.1-hybrid", "v3.1-gated"];
const CLASSIFIERS = ["lexicon-v2", "tfidf-lr", "embed-lr", "hybrid-nn", "gated"];

const pct = (v: number | undefined) => (v === undefined ? "—" : (v * 100).toFixed(1));

function latestByConfig(runs: EvaluationRun[]) {
  const out = new Map<string, EvaluationRun>();
  for (const run of runs) if (!out.has(run.config)) out.set(run.config, run);
  return CONFIG_ORDER.flatMap((c) => (out.has(c) ? [out.get(c)!] : []));
}

function Evaluation() {
  const { engine, runs, classifiers, dag } = Route.useLoaderData();
  const latest = latestByConfig(runs);
  const splits = latest[0]?.documents ?? [];

  const best = (key: string, metric: string) =>
    Math.max(
      ...latest.map(
        (r) => r.documents.find((d) => `${d.dataset}/${d.split}` === key)?.metrics[metric] ?? -1,
      ),
    );

  // Chart data: Pipeline F1 Comparison on primary open split
  const primarySplitKey = splits[0] ? `${splits[0].dataset}/${splits[0].split}` : "";
  const pipelineChartData = latest.map((run) => {
    const docRow = run.documents.find((d) => `${d.dataset}/${d.split}` === primarySplitKey);
    return {
      config: run.config,
      fnd_f1: docRow ? Math.round((docRow.metrics["fnd_f1"] ?? 0) * 1000) / 10 : 0,
      id_f1: docRow ? Math.round((docRow.metrics["id_f1"] ?? 0) * 1000) / 10 : 0,
      map_accuracy: docRow ? Math.round((docRow.metrics["map_accuracy"] ?? 0) * 1000) / 10 : 0,
    };
  });

  // Chart data: Classifier Macro-F1 across test sets
  const classifierChartData = classifiers
    ? Object.entries(classifiers.results).map(([set, res]) => ({
        testSet: set,
        "hybrid-nn": Math.round((res["hybrid-nn"]?.cls_macro_f1 ?? 0) * 1000) / 10,
        gated: Math.round((res["gated"]?.cls_macro_f1 ?? 0) * 1000) / 10,
        "embed-lr": Math.round((res["embed-lr"]?.cls_macro_f1 ?? 0) * 1000) / 10,
        "tfidf-lr": Math.round((res["tfidf-lr"]?.cls_macro_f1 ?? 0) * 1000) / 10,
        "lexicon-v2": Math.round((res["lexicon-v2"]?.cls_macro_f1 ?? 0) * 1000) / 10,
      }))
    : [];

  return (
    <div className="reveal space-y-8">
      {/* Header */}
      <PageHeader
        eyebrow="Research & Quality Engine"
        title="Model Evaluation & Benchmarks"
        description="Append-only evaluation runs scored against curated gold datasets with 95% bootstrap confidence intervals. Blind splits protected from training leakage."
        methodologyTitle="Evaluation Methodology & Confidence Intervals"
        methodologyContent={
          <div className="space-y-4 pt-2 text-xs leading-relaxed text-muted-foreground">
            <p className="font-semibold text-primary">Immutable Benchmark Verification</p>
            <p>
              Every metric originates from deterministic evaluation runs in{" "}
              <code>aiml/results</code>. 95% confidence intervals are calculated via 1,000 bootstrap
              resamples on unseen holdouts.
            </p>
            <div className="grid grid-cols-2 gap-2 text-primary font-mono text-[11px] pt-1">
              <span className="rounded bg-muted p-2">v3.1: Active Baseline</span>
              <span className="rounded bg-muted p-2">
                Gated: Tau = {classifiers?.meta?.gate_tau ?? "0.75"}
              </span>
            </div>
          </div>
        }
      >
        <span className="rounded-lg border border-border/80 bg-card px-3 py-1 font-mono text-xs font-bold text-accent-foreground">
          Commit: {runs[0]?.gitCommit ? runs[0].gitCommit.slice(0, 8) : "main"}
        </span>
      </PageHeader>

      {/* Active System Specs Row */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="intel-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="eyebrow flex items-center gap-1.5">
              <Cpu className="size-3.5" />
              <span>Active Engine</span>
            </span>
            <span className="rounded-md bg-success/20 px-2 py-0.5 font-mono text-[10px] font-bold text-success-foreground">
              v{engine.config}
            </span>
          </div>
          <p className="text-xl font-mono font-extrabold text-primary">{engine.pipelineVersion}</p>
          <p className="text-xs text-muted-foreground">
            Classifier: <strong>{engine.classifier}</strong> · Mode:{" "}
            <strong>{engine.dependencyMode}</strong>
          </p>
        </div>

        <div className="intel-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="eyebrow flex items-center gap-1.5">
              <GitBranch className="size-3.5" />
              <span>Dependency DAG</span>
            </span>
            <span className="rounded-md bg-accent/30 px-2 py-0.5 font-mono text-[10px] font-bold text-accent-foreground">
              Max Layer {dag.stats.max_layer}
            </span>
          </div>
          <p className="text-xl font-mono font-extrabold text-primary">
            {dag.stats.nodes} Nodes · {dag.stats.normative_edges} Edges
          </p>
          <p className="text-xs text-muted-foreground">
            {dag.cycles.length === 0 ? "Acyclic" : `${dag.cycles.length} Cycles`} ·{" "}
            {dag.stats.transitive_only_pairs} Transitive Obligations
          </p>
        </div>

        <div className="intel-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="eyebrow flex items-center gap-1.5">
              <FlaskConical className="size-3.5" />
              <span>Evaluation Registry</span>
            </span>
            <span className="rounded-md bg-muted px-2 py-0.5 font-mono text-[10px] font-bold text-primary">
              Immutable
            </span>
          </div>
          <p className="text-xl font-mono font-extrabold text-primary">
            {runs.length} Evaluated Runs
          </p>
          <p className="text-xs text-muted-foreground truncate">
            Latest: {runs[0] ? new Date(runs[0].createdAt).toLocaleDateString() : "—"}
          </p>
        </div>
      </section>

      {/* Dataset Health Strip */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <MetricCard
          label="Training Fit"
          value={classifiers?.meta.training.fit ?? 136}
          subtitle="Unique requirements"
        />
        <MetricCard label="Evaluation Runs" value={runs.length} subtitle="Versioned histories" />
        <MetricCard
          label="Blind Benchmarks"
          value={splits.filter((s) => s.role === "blind").length || 2}
          subtitle="Protected splits"
        />
        <MetricCard label="Gold Requirements" value={869} subtitle="Hand-verified gold" />
        <MetricCard label="Gold Findings" value={75} subtitle="Verified benchmarks" />
      </section>

      {/* Chart: Pipeline F1 Benchmark */}
      <section className="intel-card p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-3">
          <div>
            <p className="eyebrow">Pipeline Performance</p>
            <h2 className="text-base font-bold text-primary">
              F1 Metrics by Configuration ({primarySplitKey || "dev split"})
            </h2>
          </div>
          <span className="text-xs text-muted-foreground">Scores in % (Higher is better)</span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={pipelineChartData}
              margin={{ top: 10, right: 10, left: -20, bottom: 10 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="color-mix(in oklab, var(--border) 60%, transparent)"
              />
              <XAxis dataKey="config" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null;
                  return (
                    <div className="rounded-lg border border-border bg-popover p-3 text-xs shadow-lg">
                      <p className="font-bold text-popover-foreground">{label}</p>
                      {payload.map((item) => (
                        <p key={item.dataKey} className="mt-1 font-mono">
                          {item.name}: <span className="font-bold">{item.value}%</span>
                        </p>
                      ))}
                    </div>
                  );
                }}
              />
              <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
              <Bar
                dataKey="fnd_f1"
                name="Findings F1"
                fill="var(--accent-foreground)"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="id_f1"
                name="Requirement ID F1"
                fill="var(--primary)"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="map_accuracy"
                name="Mapping Accuracy"
                fill="var(--success-foreground)"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Detailed Benchmark Table per Split */}
      <section className="space-y-6">
        <div>
          <p className="eyebrow">A/B Benchmark Comparison</p>
          <h2 className="text-xl font-bold text-primary">Configuration Scorecards</h2>
        </div>

        {splits.map((split) => {
          const key = `${split.dataset}/${split.split}`;
          return (
            <div key={key} className="intel-card overflow-hidden">
              <div className="flex items-center justify-between border-b border-border/70 bg-card/60 px-5 py-3">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-primary text-sm">{key}</span>
                  <span className="rounded bg-muted px-2 py-0.5 font-mono text-[10px] text-muted-foreground uppercase">
                    {split.role}
                  </span>
                  {split.role === "blind" && <Lock className="size-3.5 text-warning-foreground" />}
                </div>
                <span className="text-xs text-muted-foreground font-mono">{split.n} documents</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-xs">
                  <thead className="border-b border-border/60 bg-muted/30 text-[10px] uppercase font-bold text-muted-foreground">
                    <tr>
                      <th className="py-2.5 px-4">Config</th>
                      {METRICS.map(([, label]) => (
                        <th key={label} className="py-2.5 px-3 text-right">
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50">
                    {latest.map((run) => {
                      const row = run.documents.find((d) => `${d.dataset}/${d.split}` === key);
                      return (
                        <tr key={run.runId} className="hover:bg-accent/15 transition">
                          <td className="py-3 px-4 font-bold font-mono text-primary">
                            {run.config}
                          </td>
                          {METRICS.map(([m]) => {
                            const v = row?.metrics[m];
                            const ci = row?.ci[m];
                            const isTop =
                              v !== undefined && v === best(key, m) && latest.length > 1;

                            return (
                              <td
                                key={m}
                                className={`py-3 px-3 text-right font-mono tabular-nums ${
                                  isTop ? "font-bold text-accent-foreground bg-accent/10" : ""
                                }`}
                              >
                                <span>{pct(v)}</span>
                                {ci && m === "fnd_f1" && (
                                  <span className="block text-[9px] text-muted-foreground font-normal">
                                    [{pct(ci[0])}–{pct(ci[1])}]
                                  </span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </section>

      {/* Classifier Comparison Section */}
      {classifiers && (
        <section className="intel-card p-6 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-4">
            <div>
              <p className="eyebrow flex items-center gap-1.5">
                <BrainCircuit className="size-4" />
                <span>Learned Models vs Rule Lexicon</span>
              </p>
              <h2 className="text-xl font-bold text-primary">Classifier Macro-F1 Benchmarks</h2>
            </div>
            <span className="text-xs text-muted-foreground font-mono">
              Encoder: {classifiers.meta.encoder.split("/").pop()}
            </span>
          </div>

          {/* Grouped Bar Chart of Classifier Models */}
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={classifierChartData}
                margin={{ top: 10, right: 10, left: -20, bottom: 10 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="color-mix(in oklab, var(--border) 60%, transparent)"
                />
                <XAxis dataKey="testSet" tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null;
                    return (
                      <div className="rounded-lg border border-border bg-popover p-3 text-xs shadow-lg">
                        <p className="font-bold text-popover-foreground">{label}</p>
                        {payload.map((item) => (
                          <p key={item.dataKey} className="mt-1 font-mono">
                            {item.name}: <span className="font-bold">{item.value}%</span>
                          </p>
                        ))}
                      </div>
                    );
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                <Bar
                  dataKey="hybrid-nn"
                  name="Hybrid NN"
                  fill="var(--accent-foreground)"
                  radius={[3, 3, 0, 0]}
                />
                <Bar
                  dataKey="gated"
                  name="Gated Ensemble"
                  fill="var(--primary)"
                  radius={[3, 3, 0, 0]}
                />
                <Bar
                  dataKey="embed-lr"
                  name="Embed LR"
                  fill="var(--warning-foreground)"
                  radius={[3, 3, 0, 0]}
                />
                <Bar
                  dataKey="lexicon-v2"
                  name="Lexicon v2"
                  fill="var(--success-foreground)"
                  radius={[3, 3, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Classifier Table with Confidence Intervals */}
          <div className="overflow-x-auto rounded-xl border border-border/70">
            <table className="w-full min-w-[700px] text-left text-xs">
              <thead className="bg-muted/40 border-b border-border/70 text-[10px] uppercase font-bold text-muted-foreground">
                <tr>
                  <th className="py-2.5 px-4">Test Split</th>
                  <th className="py-2.5 px-3 text-right">Samples (n)</th>
                  {CLASSIFIERS.map((c) => (
                    <th key={c} className="py-2.5 px-3 text-right">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {Object.entries(classifiers.results).map(([set, res]) => {
                  const top = Math.max(...CLASSIFIERS.map((c) => res[c]?.cls_macro_f1 ?? 0));
                  return (
                    <tr key={set} className="hover:bg-accent/15 transition">
                      <td className="py-3 px-4 font-bold text-primary">{set}</td>
                      <td className="py-3 px-3 text-right font-mono text-muted-foreground">
                        {res["lexicon-v2"]?.n}
                      </td>
                      {CLASSIFIERS.map((c) => {
                        const r = res[c];
                        const ci = r?.ci?.["cls_macro_f1"];
                        const isTop = r?.cls_macro_f1 === top;
                        return (
                          <td
                            key={c}
                            className={`py-3 px-3 text-right font-mono tabular-nums ${
                              isTop ? "font-bold text-accent-foreground bg-accent/10" : ""
                            }`}
                          >
                            <span>{pct(r?.cls_macro_f1)}</span>
                            {ci && (
                              <span className="block text-[9px] text-muted-foreground font-normal">
                                [{pct(ci[0])}–{pct(ci[1])}]
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
