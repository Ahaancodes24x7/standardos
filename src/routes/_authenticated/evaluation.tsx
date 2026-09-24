import { createFileRoute } from "@tanstack/react-router";
import { BrainCircuit, Cpu, FlaskConical, GitBranch, Lock } from "lucide-react";
import type { EvaluationRun } from "@/lib/contracts";
import {
  getClassifierComparison,
  getDependencyDag,
  getEngineInfo,
  listEvaluationRuns,
} from "@/services/analysis";

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
      { title: "Model Evaluation — STANDARDOS" },
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

/** Latest run of each headline configuration. */
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

  return (
    <div className="reveal">
      <header>
        <p className="eyebrow">Workspace / Quality</p>
        <h1 className="page-title mt-3">Model Evaluation</h1>
        <p className="mt-4 max-w-3xl leading-7 text-muted-foreground">
          Every number here comes from a versioned, append-only evaluation run in{" "}
          <code>aiml/results</code>, scored against hand-checked gold with 95% bootstrap confidence
          intervals. Blind splits are never used for development; each time one is scored it is
          logged.
        </p>
      </header>

      <section className="mt-10 grid gap-4 md:grid-cols-3">
        <div className="glass-panel p-5">
          <p className="eyebrow flex items-center gap-2">
            <Cpu className="size-4" /> Active engine
          </p>
          <p className="mt-3 font-semibold text-primary">{engine.pipelineVersion}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Preset <b>{engine.config}</b> · classifier <b>{engine.classifier}</b>
            {engine.classifierAvailable === false ? " (unavailable — lexicon fallback)" : ""} ·
            dependencies <b>{engine.dependencyMode}</b>
          </p>
        </div>
        <div className="glass-panel p-5">
          <p className="eyebrow flex items-center gap-2">
            <GitBranch className="size-4" /> Dependency DAG
          </p>
          <p className="mt-3 font-semibold text-primary">
            {dag.stats.nodes} standards · {dag.stats.normative_edges} normative edges
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {dag.cycles.length ? `${dag.cycles.length} cycle(s) to curate` : "Acyclic"} · depth{" "}
            {dag.stats.max_layer} · {Object.keys(dag.contracted).length} superseded editions
            contracted · {dag.stats.transitive_only_pairs} transitive-only obligations
          </p>
        </div>
        <div className="glass-panel p-5">
          <p className="eyebrow flex items-center gap-2">
            <FlaskConical className="size-4" /> Runs recorded
          </p>
          <p className="mt-3 font-semibold text-primary">{runs.length} evaluation runs</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Latest {runs[0] ? new Date(runs[0].createdAt).toLocaleString() : "—"} · commit{" "}
            {runs[0]?.gitCommit ?? "—"}
          </p>
        </div>
      </section>

      <section className="mt-12">
        <h2 className="font-serif text-3xl text-primary">Pipeline configurations</h2>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
          Document-level scores (TXT format) per dataset split. <b>legacy-2.1</b> reproduces the
          engine before the audit; <b>v3</b> the audit fixes; <b>v3.1</b> (default) adds the
          generalisation fixes found on the open <i>dev2</i> split; the other rows change one
          component. Best value per column in bold.
        </p>
        {splits.map((split) => {
          const key = `${split.dataset}/${split.split}`;
          return (
            <div key={key} className="glass-panel mt-6 overflow-x-auto">
              <p className="flex items-center gap-2 border-b border-border px-4 py-3 text-sm font-semibold text-primary">
                {key}
                <span className="text-xs font-normal text-muted-foreground">
                  {split.n} documents · {split.role}
                </span>
                {split.role === "blind" && <Lock className="size-3 text-muted-foreground" />}
              </p>
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-muted/55 text-xs uppercase tracking-[.06em] text-muted-foreground">
                  <tr>
                    <th className="p-3">Config</th>
                    {METRICS.map(([, label]) => (
                      <th key={label} className="p-3 text-right">
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {latest.map((run) => {
                    const row = run.documents.find((d) => `${d.dataset}/${d.split}` === key);
                    return (
                      <tr key={run.runId} className="border-t border-border">
                        <td className="p-3 font-semibold">{run.config}</td>
                        {METRICS.map(([m]) => {
                          const v = row?.metrics[m];
                          const ci = row?.ci[m];
                          const top = v !== undefined && v === best(key, m) && latest.length > 1;
                          return (
                            <td
                              key={m}
                              className={`p-3 text-right tabular-nums ${top ? "font-bold text-primary" : ""}`}
                            >
                              {pct(v)}
                              {ci && m === "fnd_f1" ? (
                                <span className="block text-[10px] font-normal text-muted-foreground">
                                  [{pct(ci[0])}–{pct(ci[1])}]
                                </span>
                              ) : null}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          );
        })}
      </section>

      {classifiers && (
        <section className="mt-12">
          <h2 className="flex items-center gap-2 font-serif text-3xl text-primary">
            <BrainCircuit className="size-7" /> Requirement classifiers
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
            The rule lexicon compared with learned models trained on {classifiers.meta.training.fit}{" "}
            unique requirements from open splits ({classifiers.meta.training.datasets.join(", ")}).{" "}
            <b>hybrid-nn</b> fuses a frozen <code>{classifiers.meta.encoder.split("/").pop()}</code>{" "}
            sentence embedding with the NLP layer's symbolic features; <b>gated</b> keeps the
            lexicon when its confidence ≥ τ = {classifiers.meta.gate_tau.toFixed(3)}. Macro-F1 with
            95% CI on wording the models never saw.
          </p>
          <div className="glass-panel mt-6 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-muted/55 text-xs uppercase tracking-[.06em] text-muted-foreground">
                <tr>
                  <th className="p-3">Test set</th>
                  <th className="p-3 text-right">n</th>
                  {CLASSIFIERS.map((c) => (
                    <th key={c} className="p-3 text-right">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(classifiers.results).map(([set, res]) => {
                  const top = Math.max(...CLASSIFIERS.map((c) => res[c]?.cls_macro_f1 ?? 0));
                  return (
                    <tr key={set} className="border-t border-border">
                      <td className="p-3 font-semibold">{set}</td>
                      <td className="p-3 text-right tabular-nums">{res["lexicon-v2"]?.n}</td>
                      {CLASSIFIERS.map((c) => {
                        const r = res[c];
                        const ci = r?.ci?.["cls_macro_f1"];
                        return (
                          <td
                            key={c}
                            className={`p-3 text-right tabular-nums ${r?.cls_macro_f1 === top ? "font-bold text-primary" : ""}`}
                          >
                            {pct(r?.cls_macro_f1)}
                            {ci ? (
                              <span className="block text-[10px] font-normal text-muted-foreground">
                                [{pct(ci[0])}–{pct(ci[1])}]
                              </span>
                            ) : null}
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
