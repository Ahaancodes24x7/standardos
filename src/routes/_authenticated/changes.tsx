import { createFileRoute, Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowRight,
  ArrowRightCircle,
  CalendarClock,
  Clock,
  ExternalLink,
  FileText,
  GitBranch,
  Layers,
  Scale,
  ShieldAlert,
} from "lucide-react";
import { getChangeImpact } from "@/services/analysis";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";

export const Route = createFileRoute("/_authenticated/changes")({
  loader: () => getChangeImpact(),
  head: () => ({
    meta: [
      { title: "Change Impact — STANDARDOS" },
      {
        name: "description",
        content: "Trace Indian Standard amendments to affected procurement specifications.",
      },
      { property: "og:title", content: "Change Impact — STANDARDOS" },
      {
        property: "og:description",
        content: "See which procurement requirements are affected by standards changes.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ChangeImpact,
});

function ChangeImpact() {
  const changeEvents = Route.useLoaderData();

  const totalAffectedDocs = changeEvents.reduce((sum, e) => sum + e.affected.length, 0);
  const highSeverityEvents = changeEvents.filter((e) => e.severity === "high").length;

  return (
    <div className="reveal space-y-8">
      {/* Header */}
      <PageHeader
        eyebrow="Workspace / Monitoring"
        title="Change Impact Intelligence"
        description="Automatic impact cascade: when an Indian Standard is revised or amended, StandardOS traces the change through the normative DAG to every affected requirement and specification."
      />

      {/* Impact Overview Strip */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="intel-card p-5">
          <p className="eyebrow">Tracked Amendments</p>
          <p className="mt-2 text-3xl font-extrabold text-primary">{changeEvents.length}</p>
          <p className="mt-1 text-xs text-muted-foreground">Version records in knowledge corpus</p>
        </div>
        <div className="intel-card p-5">
          <p className="eyebrow">Affected Specifications</p>
          <p className="mt-2 text-3xl font-extrabold text-primary">{totalAffectedDocs}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Specifications requiring evidence review
          </p>
        </div>
        <div className="intel-card p-5">
          <p className="eyebrow">High Priority Changes</p>
          <p className="mt-2 text-3xl font-extrabold text-destructive">{highSeverityEvents}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Immediate specification revision advised
          </p>
        </div>
      </div>

      {/* Timeline of Amendment Events */}
      <div className="space-y-6">
        {changeEvents.map((event) => {
          const directCount = event.affected.filter((a) => !a.via).length;
          const indirectCount = event.affected.filter((a) => a.via).length;

          return (
            <article key={event.id} className="intel-card p-6 space-y-6">
              {/* Event Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-4">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-mono text-xl font-extrabold text-primary">
                    {event.standard}
                  </span>
                  <StatusBadge status={event.severity} type="severity" size="sm" />
                  <span className="rounded bg-accent/30 px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-accent-foreground">
                    {event.change}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                  <CalendarClock className="size-4" />
                  <span>{event.date}</span>
                </div>
              </div>

              {/* Summary */}
              <p className="text-sm font-medium leading-relaxed text-primary">{event.summary}</p>

              {/* Visual Cascade Flow */}
              <div className="rounded-xl border border-border/80 bg-background/60 p-4">
                <p className="eyebrow mb-3">Normative Impact Cascade</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center text-xs">
                  <div className="rounded-lg border border-border/70 bg-card p-3 space-y-1">
                    <span className="text-[10px] font-bold uppercase text-muted-foreground">
                      Amended Standard
                    </span>
                    <p className="font-mono font-bold text-accent-foreground">{event.standard}</p>
                  </div>
                  <div className="rounded-lg border border-border/70 bg-card p-3 space-y-1">
                    <span className="text-[10px] font-bold uppercase text-muted-foreground">
                      Dependent Obligations
                    </span>
                    <p className="font-mono font-bold text-primary">
                      {indirectCount > 0
                        ? `${indirectCount} Indirect Standards`
                        : "Direct Normative"}
                    </p>
                  </div>
                  <div className="rounded-lg border border-border/70 bg-card p-3 space-y-1">
                    <span className="text-[10px] font-bold uppercase text-muted-foreground">
                      Impacted Specifications
                    </span>
                    <p className="font-mono font-bold text-primary">
                      {event.affected.length} Documents
                    </p>
                  </div>
                </div>
              </div>

              {/* Affected Specifications List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    Affected Specifications in Workspace ({event.affected.length})
                  </p>
                  <Button
                    asChild
                    size="sm"
                    variant="ghost"
                    className="h-6 gap-1 text-xs text-accent-foreground"
                  >
                    <Link to="/standard/$id" params={{ id: event.standardId }}>
                      <span>View standard record</span>
                      <ExternalLink className="size-3" />
                    </Link>
                  </Button>
                </div>

                {!event.affected.length ? (
                  <p className="rounded-lg border border-dashed border-border p-4 text-center text-xs text-muted-foreground">
                    No analyzed specifications in this workspace map to this standard.
                  </p>
                ) : (
                  <div className="divide-y divide-border/60 rounded-xl border border-border/70 bg-card/60 overflow-hidden">
                    {event.affected.map(({ name, documentId, via }) => (
                      <div
                        key={name}
                        className="flex flex-wrap items-center justify-between gap-4 p-4 text-xs hover:bg-accent/20 transition"
                      >
                        <div className="flex items-start gap-3 min-w-0">
                          <FileText className="size-4 text-accent-foreground shrink-0 mt-0.5" />
                          <div className="min-w-0">
                            <p className="font-bold text-primary truncate">{name}</p>
                            <p className="mt-0.5 text-[11px] text-muted-foreground">
                              {via ? (
                                <span className="text-warning-foreground font-semibold">
                                  Indirect: relies on {via} which normatively requires{" "}
                                  {event.standard}
                                </span>
                              ) : (
                                "Direct normative reference: review the mapped requirement evidence"
                              )}
                            </p>
                          </div>
                        </div>

                        {documentId ? (
                          <Button
                            asChild
                            size="sm"
                            variant="outline"
                            className="gap-1.5 h-7 text-xs"
                          >
                            <Link to="/documents/$documentId" params={{ documentId }}>
                              <span>Review Spec</span>
                              <ArrowRight className="size-3" />
                            </Link>
                          </Button>
                        ) : (
                          <span className="flex items-center gap-1 text-[11px] font-semibold text-warning-foreground">
                            <AlertTriangle className="size-3.5" />
                            <span>Sample Document</span>
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
