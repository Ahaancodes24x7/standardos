import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import {
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  GitBranch,
  History,
  Link2,
  ShieldCheck,
  Waypoints,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { getStandard, getStandardDependencies } from "@/services/analysis";
import { PageHeader } from "@/components/shared/page-header";

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
        { title: `${title} — STANDARDOS` },
        { name: "description", content: loaderData?.standard.scope ?? "Indian Standard detail." },
        { property: "og:title", content: `${title} — STANDARDOS` },
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
    <div className="reveal site-container py-8 space-y-8">
      {/* Back button */}
      <div>
        <Button asChild variant="ghost" size="sm" className="gap-1.5 px-0 text-xs">
          <Link to="/standards">
            <ArrowLeft className="size-3.5" />
            <span>Back to Standards & DAG</span>
          </Link>
        </Button>
      </div>

      {/* Header */}
      <PageHeader
        eyebrow={`Indian Standard · Edition ${standard.year}${standard.status ? ` · ${standard.status}` : ""}`}
        title={`${standard.number}`}
        description={standard.title}
      >
        <span
          className={`rounded-lg px-3 py-1 font-mono text-xs font-bold uppercase tracking-wider ${
            standard.status === "Superseded" || standard.status === "Withdrawn"
              ? "bg-warning/20 text-warning-foreground"
              : "bg-success/20 text-success-foreground"
          }`}
        >
          {standard.status || "Active Publication"}
        </span>
      </PageHeader>

      <div className="grid gap-8 lg:grid-cols-12">
        {/* Main Content */}
        <div className="space-y-8 lg:col-span-8">
          {/* Scope Card */}
          <section className="intel-card p-6 space-y-3">
            <p className="eyebrow">Normative Scope</p>
            <p className="text-sm leading-relaxed text-primary">{standard.scope}</p>
          </section>

          {/* Clauses */}
          <section className="space-y-4">
            <div className="flex items-center justify-between border-b border-border/70 pb-3">
              <div>
                <p className="eyebrow">Clause Index</p>
                <h2 className="text-xl font-bold text-primary">Indexed Provisions</h2>
              </div>
              <span className="text-xs text-muted-foreground font-mono">
                {standard.clauses.length} Clauses
              </span>
            </div>

            <div className="grid gap-3">
              {standard.clauses.map((clause) => (
                <div key={clause.id} className="intel-card p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-accent/20 px-2 py-0.5 font-mono text-[11px] font-bold text-accent-foreground">
                      {clause.section}
                    </span>
                  </div>
                  <p className="text-sm font-medium leading-relaxed text-primary">{clause.text}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Related Standards Graph */}
          <section className="space-y-4">
            <div className="flex items-center justify-between border-b border-border/70 pb-3">
              <div>
                <p className="eyebrow">Typed Graph Edges</p>
                <h2 className="text-xl font-bold text-primary">Related Standards</h2>
              </div>
              <span className="text-xs text-muted-foreground font-mono">
                {standard.relationships?.length || 0} Relationships
              </span>
            </div>

            <div className="intel-card divide-y divide-border/60 overflow-hidden">
              {standard.relationships?.map((rel) => (
                <div
                  key={rel.id}
                  className="flex flex-wrap items-center justify-between gap-3 p-4 text-xs hover:bg-accent/20 transition"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-28 shrink-0 font-bold uppercase tracking-wider text-[10px] text-muted-foreground">
                      {RELATION_LABEL[rel.type]?.[rel.direction === "out" ? 0 : 1] ?? rel.type}
                    </span>
                    <Button
                      asChild
                      variant="outline"
                      size="sm"
                      className="h-7 gap-1 font-mono text-xs"
                    >
                      <Link to="/standard/$id" params={{ id: rel.standardId }}>
                        <Link2 className="size-3" />
                        <span>{rel.number}</span>
                      </Link>
                    </Button>
                  </div>
                  <span className="text-xs text-muted-foreground text-right">
                    {rel.note} ({rel.method} · confidence {rel.confidence})
                  </span>
                </div>
              ))}
              {!standard.relationships?.length && (
                <div className="p-8 text-center text-xs text-muted-foreground">
                  No typed relationships recorded in this corpus version.
                </div>
              )}
            </div>
          </section>

          {/* Normative Dependencies from DAG */}
          {dependencies &&
            (dependencies.dependsOn.length > 0 ||
              dependencies.requiredBy.length > 0 ||
              dependencies.canonical) && (
              <section className="intel-card p-6 space-y-5">
                <div>
                  <p className="eyebrow flex items-center gap-1.5">
                    <GitBranch className="size-3.5 text-accent-foreground" />
                    <span>DAG Dependency Analysis</span>
                  </p>
                  <h2 className="text-base font-bold text-primary mt-1">
                    Transitive Normative Obligations
                  </h2>
                </div>

                {dependencies.canonical && (
                  <div className="rounded-lg border border-accent/40 bg-accent/10 p-3 text-xs text-primary">
                    Reasoned as{" "}
                    <Link
                      to="/standard/$id"
                      params={{ id: dependencies.canonical.id }}
                      className="font-mono font-bold underline"
                    >
                      {dependencies.canonical.number}
                    </Link>{" "}
                    (superseded edition contracted into current replacement).
                  </div>
                )}

                <div className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-2">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                      Depends On ({dependencies.dependsOn.length})
                    </p>
                    <div className="space-y-1.5">
                      {dependencies.dependsOn.map((d) => (
                        <div
                          key={d.id}
                          className="flex items-center justify-between rounded-lg border border-border/70 bg-background/60 p-2.5 text-xs"
                        >
                          <Link
                            to="/standard/$id"
                            params={{ id: d.id }}
                            className="font-mono font-bold text-accent-foreground hover:underline"
                          >
                            {d.number}
                          </Link>
                          <span className="text-[10px] text-muted-foreground">
                            {d.type === "TESTED_BY" ? "Test Method" : "Requires"}
                            {d.depth > 1 ? ` · Depth ${d.depth}` : ""}
                          </span>
                        </div>
                      ))}
                      {!dependencies.dependsOn.length && (
                        <p className="text-xs text-muted-foreground">No prerequisites.</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                      Required By ({dependencies.requiredBy.length})
                    </p>
                    <div className="space-y-1.5">
                      {dependencies.requiredBy.map((d) => (
                        <div
                          key={d.id}
                          className="flex items-center justify-between rounded-lg border border-border/70 bg-background/60 p-2.5 text-xs"
                        >
                          <Link
                            to="/standard/$id"
                            params={{ id: d.id }}
                            className="font-mono font-bold text-primary hover:underline"
                          >
                            {d.number}
                          </Link>
                          <span className="text-[10px] text-muted-foreground truncate max-w-[120px]">
                            {d.title}
                          </span>
                        </div>
                      ))}
                      {!dependencies.requiredBy.length && (
                        <p className="text-xs text-muted-foreground">No downstream dependents.</p>
                      )}
                    </div>
                  </div>
                </div>
              </section>
            )}
        </div>

        {/* Sidebar Info */}
        <aside className="space-y-6 lg:col-span-4">
          {/* Metadata Card */}
          <div className="intel-card p-6 space-y-4">
            <h3 className="flex items-center gap-2 text-sm font-bold text-primary border-b border-border/60 pb-3">
              <ShieldCheck className="size-4 text-accent-foreground" />
              <span>Standard Record</span>
            </h3>
            <dl className="grid gap-3 text-xs">
              <div>
                <dt className="text-muted-foreground">Domain Category</dt>
                <dd className="font-semibold text-primary">{standard.category}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Language</dt>
                <dd className="font-semibold text-primary">{standard.language}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Publication Year</dt>
                <dd className="font-mono font-semibold text-primary">{standard.year}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Corpus Verification</dt>
                <dd className="font-semibold text-primary">
                  {standard.verified ? "Verified Publication" : "Unverified Seed Metadata"}
                </dd>
              </div>
            </dl>
          </div>

          {/* Authorities */}
          <div className="intel-card p-6 space-y-3">
            <h3 className="flex items-center gap-2 text-sm font-bold text-primary border-b border-border/60 pb-3">
              <Building2 className="size-4 text-accent-foreground" />
              <span>Conformity Authorities</span>
            </h3>
            <ul className="space-y-2 text-xs">
              {standard.certificationBodies.map((body) => (
                <li
                  key={body}
                  className="rounded-lg border border-border/70 bg-background/60 p-2.5 font-medium text-primary"
                >
                  {body}
                </li>
              ))}
            </ul>
          </div>

          {/* Version History */}
          {standard.events?.length ? (
            <div className="intel-card p-6 space-y-3">
              <h3 className="flex items-center gap-2 text-sm font-bold text-primary border-b border-border/60 pb-3">
                <History className="size-4 text-accent-foreground" />
                <span>Version Records</span>
              </h3>
              <ul className="space-y-3 text-xs">
                {standard.events.map((e, i) => (
                  <li key={i} className="border-l-2 border-accent-foreground pl-3 space-y-0.5">
                    <p className="font-bold text-primary">{e.summary}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {e.kind} · {e.date || "Date unrecorded"}
                    </p>
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
