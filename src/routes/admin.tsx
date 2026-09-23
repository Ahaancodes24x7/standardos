import { createFileRoute, Link } from "@tanstack/react-router";
import { Database, Terminal } from "lucide-react";
import { PageIntro } from "@/components/app-shell";
import { getCorpusStatus } from "@/services/analysis";

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
          in <code>backend/</code>); in-app upload of licensed standards is not implemented yet.
        </p>
      </div>
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
