import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { ArrowLeft, Building2, GitBranch, History, Link2, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getStandard, getStandardDependencies } from "@/services/analysis";

const RELATION_LABEL: Record<string, [string, string]> = {
  REFERENCES: ["References", "Referenced by"],
  REQUIRES: ["Requires", "Required by"],
  TESTED_BY: ["Tested by", "Test method for"],
  SUPERSEDES: ["Supersedes", "Superseded by"],
  AMENDED_BY: ["Amended by", "Amends"],
  RELATED_TO: ["Related to", "Related to"],
  SUPPORTS: ["Supports", "Supported by"],
};

export const Route = createFileRoute("/standard/$id")({
  loader: async ({ params }) => {
    const standard = await getStandard(params.id);
    if (!standard) throw notFound();
    const dependencies = await getStandardDependencies(params.id).catch(() => null);
    return { standard, dependencies };
  },
  head: ({ loaderData }) => {
    const title = loaderData?.standard.title ?? "Standard unavailable";
    return {
      meta: [
        { title: `${title} — StandardOS` },
        { name: "description", content: loaderData?.standard.scope ?? "Indian Standard detail." },
        { property: "og:title", content: `${title} — StandardOS` },
        {
          property: "og:description",
          content: loaderData?.standard.scope ?? "Indian Standard detail.",
        },
        { property: "og:type", content: "article" },
        { name: "twitter:card", content: "summary_large_image" },
      ],
    };
  },
  component: StandardDetail,
});

function StandardDetail() {
  const { standard, dependencies } = Route.useLoaderData();
  return (
    <div className="page-wrap pb-20 pt-8">
      <Button asChild variant="ghost" className="mb-6 px-0">
        <Link to="/search">
          <ArrowLeft /> Back to results
        </Link>
      </Button>
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_18rem]">
        <article>
          <p className="eyebrow">
            Indian Standard · {standard.year}
            {standard.status ? ` · ${standard.status}` : ""}
          </p>
          <h1 className="mt-4 font-serif text-4xl leading-tight text-primary sm:text-6xl">
            {standard.number}
          </h1>
          <p className="mt-3 font-serif text-2xl leading-9 text-foreground">{standard.title}</p>
          <div className="mt-8 border-y border-border py-6">
            <h2 className="font-serif text-2xl text-primary">Scope</h2>
            <p className="mt-3 leading-7 text-muted-foreground">{standard.scope}</p>
          </div>
          <section className="mt-10">
            <h2 className="font-serif text-3xl text-primary">Clauses</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Paraphrased summaries for retrieval and explanation — not the normative text. Review
              the official publication before specifying compliance.
            </p>
            <div className="mt-5 grid gap-4">
              {standard.clauses.map((clause) => (
                <div className="glass-panel p-6" key={clause.id}>
                  <p className="eyebrow">{clause.section}</p>
                  <p className="mt-4 font-serif text-xl leading-8">{clause.text}</p>
                </div>
              ))}
            </div>
          </section>
          <section className="mt-10">
            <h2 className="font-serif text-3xl text-primary">Related standards</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Typed relationships in the standards knowledge graph.
            </p>
            <div className="mt-5 grid gap-3">
              {standard.relationships?.map((rel) => (
                <div
                  key={rel.id}
                  className="flex flex-wrap items-center gap-3 border-b border-border pb-3 text-sm"
                >
                  <span className="w-32 shrink-0 text-xs font-bold uppercase tracking-[.08em] text-muted-foreground">
                    {RELATION_LABEL[rel.type]?.[rel.direction === "out" ? 0 : 1] ?? rel.type}
                  </span>
                  <Button asChild variant="outline" size="sm">
                    <Link to="/standard/$id" params={{ id: rel.standardId }}>
                      <Link2 /> {rel.number}
                    </Link>
                  </Button>
                  <span className="min-w-0 flex-1 text-xs text-muted-foreground">
                    {rel.note} ({rel.method}, confidence {rel.confidence})
                  </span>
                </div>
              ))}
              {!standard.relationships?.length && (
                <p className="text-sm text-muted-foreground">No relationships recorded.</p>
              )}
            </div>
          </section>
          {dependencies &&
          (dependencies.dependsOn.length > 0 ||
            dependencies.requiredBy.length > 0 ||
            dependencies.canonical) ? (
            <section className="mt-10">
              <h2 className="flex items-center gap-2 font-serif text-3xl text-primary">
                <GitBranch className="size-6" /> Normative dependencies
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                From the dependency DAG (REQUIRES and TESTED_BY edges, superseded editions
                contracted into their replacements). Specifying this standard obliges its
                dependencies; a revision of it affects every standard that depends on it.
              </p>
              {dependencies.canonical && (
                <p className="mt-4 text-sm">
                  Reasoned as{" "}
                  <Link
                    className="font-semibold text-primary underline"
                    to="/standard/$id"
                    params={{ id: dependencies.canonical.id }}
                  >
                    {dependencies.canonical.number}
                  </Link>{" "}
                  (current replacement).
                </p>
              )}
              <div className="mt-5 grid gap-6 sm:grid-cols-2">
                <div>
                  <p className="eyebrow">Depends on</p>
                  <ul className="mt-3 space-y-2 text-sm">
                    {dependencies.dependsOn.map((d) => (
                      <li key={d.id} className="border-l-2 border-accent pl-3">
                        <Link
                          className="font-semibold text-primary"
                          to="/standard/$id"
                          params={{ id: d.id }}
                        >
                          {d.number}
                        </Link>{" "}
                        <span className="text-xs text-muted-foreground">
                          {d.type === "TESTED_BY" ? "test method" : "requires"}
                          {d.depth > 1 ? ` · via ${d.via.join(" → ")}` : ""}
                        </span>
                      </li>
                    ))}
                    {!dependencies.dependsOn.length && (
                      <li className="text-muted-foreground">None recorded.</li>
                    )}
                  </ul>
                </div>
                <div>
                  <p className="eyebrow">Required by</p>
                  <ul className="mt-3 space-y-2 text-sm">
                    {dependencies.requiredBy.map((d) => (
                      <li key={d.id} className="border-l-2 border-accent pl-3">
                        <Link
                          className="font-semibold text-primary"
                          to="/standard/$id"
                          params={{ id: d.id }}
                        >
                          {d.number}
                        </Link>{" "}
                        <span className="text-xs text-muted-foreground">{d.title}</span>
                      </li>
                    ))}
                    {!dependencies.requiredBy.length && (
                      <li className="text-muted-foreground">No dependants.</li>
                    )}
                  </ul>
                </div>
              </div>
            </section>
          ) : null}
        </article>
        <aside className="space-y-4">
          <div className="glass-panel p-5">
            <h2 className="flex items-center gap-2 font-serif text-xl text-primary">
              <ShieldCheck className="size-5" /> Record
            </h2>
            <dl className="mt-5 space-y-4 text-sm">
              <div>
                <dt className="text-muted-foreground">Category</dt>
                <dd className="font-semibold">{standard.category}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Language</dt>
                <dd className="font-semibold">{standard.language}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Publication</dt>
                <dd className="font-semibold">{standard.year}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Source</dt>
                <dd className="text-xs leading-5">
                  {standard.verified ? "Verified record" : "Unverified seed metadata"}.{" "}
                  {standard.sourceNote}
                </dd>
              </div>
            </dl>
          </div>
          <div className="glass-panel p-5">
            <h2 className="flex items-center gap-2 font-serif text-xl text-primary">
              <Building2 className="size-5" /> Authorities
            </h2>
            <ul className="mt-4 space-y-3 text-sm">
              {standard.certificationBodies.map((body) => (
                <li key={body} className="border-l-2 border-accent pl-3">
                  {body}
                </li>
              ))}
            </ul>
          </div>
          {standard.events?.length ? (
            <div className="glass-panel p-5">
              <h2 className="flex items-center gap-2 font-serif text-xl text-primary">
                <History className="size-5" /> Version history
              </h2>
              <ul className="mt-4 space-y-3 text-sm">
                {standard.events.map((e, i) => (
                  <li key={i} className="border-l-2 border-accent pl-3">
                    <p className="text-xs font-bold uppercase text-muted-foreground">
                      {e.kind} · {e.date ?? "date not recorded"}
                    </p>
                    <p className="mt-1">{e.summary}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}
