import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertTriangle, ArrowRight, CalendarClock, FileText } from "lucide-react";
import { getChangeImpact } from "@/services/analysis";
import { Button } from "@/components/ui/button";

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
  return (
    <div className="reveal">
      <header>
        <p className="eyebrow">Workspace / Monitoring</p>
        <h1 className="page-title mt-3">Change Impact</h1>
        <p className="mt-4 max-w-2xl leading-7 text-muted-foreground">
          When an Indian Standard changes, STANDARDOS traces the amendment to every specification
          and requirement that may need review. Events come from the version records in the
          standards corpus.
        </p>
      </header>
      <div className="mt-12 border-l border-border pl-6 sm:pl-10">
        {changeEvents.map((event) => (
          <article key={event.id} className="relative pb-12 last:pb-0">
            <span
              className={`absolute -left-[2.05rem] top-1 grid size-4 place-items-center rounded-full border-4 border-background sm:-left-[2.55rem] ${event.severity === "high" ? "bg-warning-foreground" : "bg-accent-foreground"}`}
            />
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <span className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                <CalendarClock className="size-4" />
                {event.date}
              </span>
              <span
                className={`text-xs font-bold uppercase ${event.severity === "high" ? "text-warning-foreground" : "text-accent-foreground"}`}
              >
                {event.change}
              </span>
            </div>
            <h2 className="mt-3 text-xl font-bold text-primary">{event.standard}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{event.summary}</p>
            <div className="mt-6 border-t border-border">
              <p className="eyebrow py-4">Affected specifications</p>
              {!event.affected.length && (
                <p className="pb-2 text-xs text-muted-foreground">
                  No analysed specification in this workspace maps to this standard.
                </p>
              )}
              {event.affected.map(({ name, documentId, via }) => (
                <div key={name} className="thin-row flex flex-wrap items-center gap-4 py-4">
                  <FileText className="size-5 text-accent-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-primary">{name}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {via
                        ? `Indirect: the specification relies on ${via}, which normatively depends on ${event.standard}.`
                        : "Review the mapped requirement and confirm the amended evidence basis."}
                    </p>
                  </div>
                  {documentId ? (
                    <Button asChild size="sm" variant="outline">
                      <Link to="/documents/$documentId" params={{ documentId }}>
                        Review <ArrowRight />
                      </Link>
                    </Button>
                  ) : (
                    <span className="flex items-center gap-2 text-xs font-semibold text-warning-foreground">
                      <AlertTriangle className="size-4" />
                      Sample document
                    </span>
                  )}
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
