import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { Database, Terminal, Upload } from "lucide-react";
import { PageIntro } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { getCorpusStatus, importCorpus } from "@/services/analysis";

export const Route = createFileRoute("/admin")({
  loader: () => getCorpusStatus(),
  head: () => ({
    meta: [
      { title: "Corpus Administration — StandardOS" },
      { name: "description", content: "Review and maintain the indexed Indian Standards corpus." },
      { property: "og:title", content: "Corpus Administration — StandardOS" },
      { property: "og:description", content: "Indexed standards and corpus maintenance tools." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Admin,
});

function Admin() {
  const status = Route.useLoaderData();
  return (
    <div className="page-wrap pb-20 pt-8">
      <PageIntro
        eyebrow="Corpus administration"
        title="Indexed standards"
        description="Review source coverage of the searchable standards collection."
      />
      <div className="mt-5 flex items-start gap-3 border-l-2 border-accent-foreground bg-accent/40 px-4 py-3 text-sm">
        <Terminal className="mt-0.5 size-4 shrink-0" />
        <p>
          Corpus version <b>{status.version}</b> loaded from <b>{status.source}</b>. Import and
          re-index run from the command line (<code>uv run python -m scripts.seed_standards</code>{" "}
          in <code>backend/</code>) or by uploading a corpus JSON file below (corpus administrators
          listed in <code>ADMIN_EMAILS</code>).
        </p>
      </div>
      <CorpusUpload />
      <div className="glass-panel mt-8 overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-border bg-muted/55 text-xs uppercase tracking-[.08em] text-muted-foreground">
            <tr>
              <th className="p-4">Number</th>
              <th className="p-4">Title</th>
              <th className="p-4">Status</th>
              <th className="p-4">Category</th>
              <th className="p-4">Clauses</th>
              <th className="p-4">Verified</th>
            </tr>
          </thead>
          <tbody>
            {status.standards.map((standard) => (
              <tr
                key={standard.id}
                className="border-b border-border last:border-0 hover:bg-accent/30"
              >
                <td className="p-4 font-semibold text-primary">
                  <Link to="/standard/$id" params={{ id: standard.id }}>
                    {standard.number}
                  </Link>
                </td>
                <td className="p-4">{standard.title}</td>
                <td className="p-4">{standard.status}</td>
                <td className="p-4">{standard.category}</td>
                <td className="p-4">{standard.clauses}</td>
                <td className="p-4 text-muted-foreground">{standard.verified ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
        <Database className="size-3" /> {status.standards.length} standards · {status.clauses}{" "}
        clauses · {status.relationships} relationships · {status.events} version records
      </p>
    </div>
  );
}

function CorpusUpload() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!file) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await importCorpus(file);
      setMessage({
        ok: true,
        text: `Imported corpus ${result.version}: ${result.standards} standards, ${result.clauses} clauses, ${result.relationships} relationships. New analyses use it immediately.`,
      });
      await router.invalidate();
    } catch (error) {
      setMessage({ ok: false, text: error instanceof Error ? error.message : "Import failed." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="glass-panel mt-6 flex flex-wrap items-center gap-4 p-5 text-sm">
      <Upload className="size-5 text-accent-foreground" />
      <label className="min-w-0 flex-1">
        <span className="block font-semibold text-primary">Import standards corpus</span>
        <span className="block text-xs text-muted-foreground">
          JSON with <code>standards</code>, <code>relationships</code>, <code>events</code> and{" "}
          <code>priorEditions</code> — the format of the bundled seed. Replaces the active corpus.
        </span>
        <input
          className="mt-2 block text-xs"
          type="file"
          accept="application/json,.json"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      <Button onClick={submit} disabled={!file || busy}>
        {busy ? "Importing…" : "Import"}
      </Button>
      {message && (
        <p
          className={`w-full text-xs ${message.ok ? "text-accent-foreground" : "text-destructive"}`}
        >
          {message.text}
        </p>
      )}
    </div>
  );
}
