import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, FileSearch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { workspaceStats } from "@/lib/analysis-view";
import { formatAnalyzedAt, listDocuments } from "@/services/analysis";

export const Route = createFileRoute("/_authenticated/dashboard")({
  loader: () => listDocuments(),
  head: () => ({
    meta: [
      { title: "Workspace Overview — STANDARDOS" },
      {
        name: "description",
        content: "Procurement specification readiness and recent analysis activity.",
      },
      { property: "og:title", content: "Workspace Overview — STANDARDOS" },
      {
        property: "og:description",
        content: "Review procurement specifications and compliance readiness.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: DashboardIndex,
});

function DashboardIndex() {
  const documents = Route.useLoaderData();
  const { profile, isDemo } = useAuth();
  const first = profile?.full_name.split(" ")[0] ?? "there";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const stats = workspaceStats(documents);
  const metrics = [
    [String(stats.documents), "Documents analyzed"],
    [String(stats.standardsMapped), "Standards mapped"],
    [String(stats.requireAttention), "Require attention"],
    [stats.averageReadiness === null ? "—" : `${stats.averageReadiness}%`, "Average readiness"],
  ];
  return (
    <div className="reveal">
      <header className="grid gap-6 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
        <div>
          <p className="eyebrow">
            Workspace / Overview{isDemo ? " · Demo (sample documents)" : ""}
          </p>
          <h1 className="page-title mt-3">
            {greeting}, {first}.
          </h1>
          <p className="mt-4 text-muted-foreground">
            Here’s what’s happening across your procurement specifications.
          </p>
        </div>
        <Button asChild size="lg">
          <Link to="/analyze">
            <FileSearch />
            Analyze new specification
          </Link>
        </Button>
      </header>
      <section className="mt-12 grid grid-cols-2 border-y border-border md:grid-cols-4">
        {metrics.map(([value, label], index) => (
          <div
            key={label}
            className={`py-7 ${index % 2 ? "pl-5" : ""} ${index > 0 ? "md:border-l md:pl-7" : ""}`}
          >
            <p className="font-display text-4xl text-primary sm:text-5xl">{value}</p>
            <p className="mt-2 text-xs font-semibold uppercase tracking-[.08em] text-muted-foreground">
              {label}
            </p>
          </div>
        ))}
      </section>
      <section className="mt-14">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="eyebrow">Active work</p>
            <h2 className="section-title mt-2">Recent Specifications</h2>
          </div>
          <Link
            to="/documents"
            className="flex items-center gap-2 text-sm font-bold text-accent-foreground"
          >
            View all documents <ArrowRight className="size-4" />
          </Link>
        </div>
        <div className="mt-6 border-t border-border">
          {!documents.length && (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No specifications analysed yet.{" "}
              <Link to="/analyze" className="font-bold text-accent-foreground">
                Analyze your first specification
              </Link>
              .
            </p>
          )}
          {documents.slice(0, 6).map((doc) => (
            <Link
              key={doc.id}
              to="/documents/$documentId"
              params={{ documentId: doc.id }}
              className="thin-row grid gap-4 py-5 lg:grid-cols-[minmax(0,2fr)_repeat(4,minmax(5rem,.65fr))_auto] lg:items-center"
            >
              <div className="min-w-0">
                <p className="truncate font-bold text-primary">{doc.name}</p>
                <p className="mt-1 text-xs text-muted-foreground">{doc.organization}</p>
              </div>
              <Meta label="Status" value={doc.status} />
              <Meta label="Standards" value={String(doc.standards)} />
              <Meta label="Issues" value={String(doc.issues)} warning={doc.issues > 2} />
              <Meta
                label="Readiness"
                value={doc.runStatus === "succeeded" ? `${doc.readiness}%` : "—"}
              />
              <span className="text-xs text-muted-foreground lg:text-right">
                {formatAnalyzedAt(doc.analyzedAt)}
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function Meta({
  label,
  value,
  warning = false,
}: {
  label: string;
  value: string;
  warning?: boolean;
}) {
  return (
    <div>
      <p className="text-[10px] font-bold uppercase tracking-[.08em] text-muted-foreground">
        {label}
      </p>
      <p
        className={`mt-1 text-sm font-semibold ${warning ? "text-warning-foreground" : "text-primary"}`}
      >
        {value}
      </p>
    </div>
  );
}
