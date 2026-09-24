import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Database,
  ExternalLink,
  FileCheck,
  FileUp,
  Layers,
  Search,
  Terminal,
  Upload,
  UploadCloud,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getCorpusStatus, importCorpus } from "@/services/analysis";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";

export const Route = createFileRoute("/admin")({
  loader: () => getCorpusStatus(),
  head: () => ({
    meta: [
      { title: "Corpus Administration — STANDARDOS" },
      { name: "description", content: "Review and maintain the indexed Indian Standards corpus." },
      { property: "og:title", content: "Corpus Administration — STANDARDOS" },
      { property: "og:description", content: "Indexed standards and corpus maintenance tools." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Admin,
});

function Admin() {
  const status = Route.useLoaderData();
  const [query, setQuery] = useState("");

  const filteredStandards = useMemo(() => {
    return status.standards.filter((s) =>
      (s.number + s.title + s.category).toLowerCase().includes(query.toLowerCase()),
    );
  }, [status.standards, query]);

  return (
    <div className="reveal site-container py-8 space-y-8">
      {/* Header */}
      <PageHeader
        eyebrow="Corpus Administration"
        title="Indexed Standards & Knowledge Base"
        description="Monitor source coverage, maintain knowledge graph relationships, and import versioned BIS corpus updates."
      >
        <span className="rounded-lg border border-border/80 bg-card px-3 py-1 font-mono text-xs font-bold text-accent-foreground">
          Corpus v{status.version} ({status.source})
        </span>
      </PageHeader>

      {/* CLI Instruction Banner */}
      <div className="flex items-start gap-3 rounded-xl border border-accent/40 bg-accent/15 p-4 text-xs">
        <Terminal className="mt-0.5 size-4 shrink-0 text-accent-foreground" />
        <div className="space-y-1">
          <p className="font-bold text-primary">Command Line Maintenance</p>
          <p className="text-muted-foreground leading-relaxed">
            Re-indexing can also be initiated via backend CLI:{" "}
            <code className="rounded bg-background px-1.5 py-0.5 font-mono text-primary font-bold">
              uv run python -m scripts.seed_standards
            </code>{" "}
            in <code>backend/</code>. Manual JSON uploads below are restricted to verified corpus
            administrators.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricCard
          label="Indexed Standards"
          value={status.standards.length}
          icon={Database}
          subtitle="BIS publications"
        />
        <MetricCard
          label="Governing Clauses"
          value={status.clauses}
          icon={Layers}
          subtitle="Indexed normative sections"
        />
        <MetricCard
          label="Graph Edges"
          value={status.relationships}
          icon={Layers}
          subtitle="Typed relationships in DAG"
        />
        <MetricCard
          label="Version Events"
          value={status.events}
          icon={FileCheck}
          subtitle="Historical amendment records"
        />
      </section>

      {/* Corpus Import Dropzone */}
      <CorpusUpload />

      {/* Standards Catalog Table */}
      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-3">
          <div>
            <p className="eyebrow">Corpus Inventory</p>
            <h2 className="text-xl font-bold text-primary">All Indexed Standards</h2>
          </div>

          <div className="relative w-64">
            <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search standards index..."
              className="h-8 pl-8 text-xs bg-background"
            />
          </div>
        </div>

        <div className="intel-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-xs">
              <thead className="border-b border-border/70 bg-muted/40 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="py-3 px-4">Standard</th>
                  <th className="py-3 px-3">Title</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Clauses</th>
                  <th className="py-3 px-4 text-right">Verification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {filteredStandards.map((standard) => (
                  <tr key={standard.id} className="hover:bg-accent/20 transition">
                    <td className="py-3 px-4 font-mono font-bold text-accent-foreground">
                      <Link
                        to="/standard/$id"
                        params={{ id: standard.id }}
                        className="hover:underline"
                      >
                        {standard.number}
                      </Link>
                    </td>
                    <td className="py-3 px-3 font-medium text-primary max-w-sm truncate">
                      {standard.title}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`rounded px-1.5 py-0.5 font-bold uppercase text-[9px] ${
                          standard.status === "Superseded" || standard.status === "Withdrawn"
                            ? "bg-warning/20 text-warning-foreground"
                            : "bg-success/20 text-success-foreground"
                        }`}
                      >
                        {standard.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-muted-foreground">{standard.category}</td>
                    <td className="py-3 px-3 font-mono font-semibold">{standard.clauses}</td>
                    <td className="py-3 px-4 text-right">
                      <span
                        className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-bold ${
                          standard.verified
                            ? "bg-success/20 text-success-foreground"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {standard.verified ? "Verified" : "Seed"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}

function CorpusUpload() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);

  const validateAndSet = (candidate: File) => {
    if (!candidate.name.toLowerCase().endsWith(".json")) {
      setMessage({ ok: false, text: "Upload a valid JSON corpus file." });
      return;
    }
    setMessage(null);
    setFile(candidate);
  };

  async function submit() {
    if (!file) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await importCorpus(file);
      setMessage({
        ok: true,
        text: `Successfully imported corpus ${result.version}: ${result.standards} standards, ${result.clauses} clauses, ${result.relationships} relationships. New analyses apply it immediately.`,
      });
      setFile(null);
      await router.invalidate();
    } catch (error) {
      setMessage({ ok: false, text: error instanceof Error ? error.message : "Import failed." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="intel-card p-6 space-y-4">
      <div>
        <p className="eyebrow">Corpus Maintenance</p>
        <h2 className="text-base font-bold text-primary">Import Standards Corpus JSON</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Upload JSON seed files with <code>standards</code>, <code>relationships</code>, and{" "}
          <code>events</code> to replace or expand the active knowledge graph.
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          const dropped = e.dataTransfer.files[0];
          if (dropped) validateAndSet(dropped);
        }}
        className={`grid min-h-36 place-items-center rounded-xl border-2 border-dashed p-6 text-center transition ${
          drag ? "border-accent-foreground bg-accent/20" : "border-border/80 bg-background/50"
        }`}
      >
        <div className="space-y-2">
          <UploadCloud className="mx-auto size-8 text-accent-foreground" />
          <p className="text-xs font-bold text-primary">
            {file ? file.name : "Drag & drop corpus JSON file here"}
          </p>
          <p className="text-[11px] text-muted-foreground">
            {file
              ? `${(file.size / 1024).toFixed(1)} KB · Ready to import`
              : "JSON schema format · Seed metadata"}
          </p>
          <div className="pt-1">
            <input
              id="admin-corpus-file"
              type="file"
              accept="application/json,.json"
              className="sr-only"
              onChange={(e) => {
                const chosen = e.target.files?.[0];
                if (chosen) validateAndSet(chosen);
              }}
            />
            <label
              htmlFor="admin-corpus-file"
              className="inline-flex cursor-pointer items-center rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-semibold text-primary hover:bg-muted"
            >
              Browse JSON file
            </label>
          </div>
        </div>
      </div>

      {file && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">
            Selected: <strong className="text-primary font-mono">{file.name}</strong>
          </span>
          <Button onClick={submit} disabled={busy} size="sm" className="gap-2">
            <FileUp className="size-3.5" />
            <span>{busy ? "Importing Corpus..." : "Import Corpus"}</span>
          </Button>
        </div>
      )}

      {message && (
        <div
          role="alert"
          className={`flex items-center gap-2 rounded-lg border p-3 text-xs font-semibold ${
            message.ok
              ? "border-success/40 bg-success/10 text-success-foreground"
              : "border-destructive/40 bg-destructive/10 text-destructive"
          }`}
        >
          {message.ok ? (
            <CheckCircle2 className="size-4 shrink-0" />
          ) : (
            <AlertCircle className="size-4 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}
    </section>
  );
}
