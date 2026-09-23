import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { FindingsList } from "@/components/analysis/findings";
import { useReviewActions } from "@/components/analysis/use-review";
import { Button } from "@/components/ui/button";
import { getAnalysis } from "@/services/analysis";

export const Route = createFileRoute("/_authenticated/documents/$documentId")({
  loader: async ({ params }) => {
    const document = await getAnalysis(params.documentId);
    if (!document) throw notFound();
    return document;
  },
  component: Detail,
});

function Detail() {
  const doc = Route.useLoaderData();
  const { onReview } = useReviewActions([doc]);
  const open = doc.findings.filter((f) => f.status !== "verified");
  return (
    <div className="reveal">
      <Link
        to="/documents"
        className="flex items-center gap-2 text-sm font-bold text-muted-foreground"
      >
        <ArrowLeft className="size-4" />
        Document library
      </Link>
      <header className="mt-7">
        <p className="eyebrow">
          {doc.type} · {doc.organization}
        </p>
        <h1 className="mt-3 font-display text-4xl text-primary sm:text-5xl">{doc.name}</h1>
        <div className="mt-7 grid grid-cols-3 border-y border-border py-5">
          <Stat value={`${doc.readiness}%`} label="Readiness" />
          <Stat value={String(doc.standards)} label="Standards" />
          <Stat value={String(doc.issues)} label="Issues" />
        </div>
      </header>
      <section className="mt-12">
        <p className="eyebrow">Extracted content</p>
        <h2 className="section-title mt-2">Key Requirements</h2>
        <div className="mt-6 border-t border-border">
          {doc.requirements.length === 0 && (
            <p className="py-8 text-sm text-muted-foreground">
              No requirements were identified in this document.
            </p>
          )}
          {doc.requirements.map((r) => (
            <article key={r.id} className="thin-row grid gap-4 py-5 md:grid-cols-[1.5fr_1fr]">
              <div>
                <p className="text-sm font-semibold leading-6 text-primary">{r.text}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {r.category}
                  {r.sectionLabel ? ` · ${r.sectionLabel}` : ""}
                </p>
              </div>
              <div className="text-sm">
                <p className="font-bold text-accent-foreground">{r.standard}</p>
                <p className="mt-1 text-muted-foreground">{r.clause}</p>
                {r.confidence !== undefined && (
                  <p className="mt-1 text-xs text-muted-foreground" title={r.explanation}>
                    {r.basis === "explicit_reference"
                      ? "Cited in the requirement"
                      : `Retrieved · ${Math.round(r.confidence * 100)}% confidence`}
                  </p>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
      <section className="mt-12">
        <p className="eyebrow">Compliance</p>
        <h2 className="section-title mt-2">Open Findings</h2>
        <div className="mt-6">
          <FindingsList findings={open} onReview={onReview} />
        </div>
      </section>
      <Button asChild className="mt-10">
        <Link to="/analyze/$documentId" params={{ documentId: doc.id }}>
          Open full analysis <ArrowRight />
        </Link>
      </Button>
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="font-display text-3xl text-primary">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
