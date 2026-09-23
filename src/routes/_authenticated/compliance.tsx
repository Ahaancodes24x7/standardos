import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { FindingsList } from "@/components/analysis/findings";
import { useReviewActions } from "@/components/analysis/use-review";
import type { FindingStatus } from "@/lib/contracts";
import { listDocuments } from "@/services/analysis";

export const Route = createFileRoute("/_authenticated/compliance")({
  loader: () => listDocuments(),
  head: () => ({
    meta: [
      { title: "Compliance Audit — STANDARDOS" },
      {
        name: "description",
        content: "Review verified, missing, conflicting, outdated, and certification findings.",
      },
      { property: "og:title", content: "Compliance Audit — STANDARDOS" },
      { property: "og:description", content: "Actionable procurement compliance findings." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Compliance,
});

const STATUSES: FindingStatus[] = [
  "verified",
  "missing",
  "conflicting",
  "outdated",
  "certification",
];

function Compliance() {
  const documents = Route.useLoaderData();
  const { onReview } = useReviewActions(documents);
  const [filter, setFilter] = useState<FindingStatus | null>(null);
  const findings = documents.flatMap((d) => d.findings);
  const counts = STATUSES.map(
    (status) => [status, findings.filter((f) => f.status === status).length] as const,
  );
  const shown = filter ? findings.filter((f) => f.status === filter) : findings;
  return (
    <div className="reveal">
      <header>
        <p className="eyebrow">Workspace / Audit</p>
        <h1 className="page-title mt-3">Compliance Findings</h1>
        <p className="mt-4 max-w-2xl text-muted-foreground">
          Every flag links the source requirement to governing evidence and a practical next action.
        </p>
      </header>
      <div className="mt-9 flex flex-wrap gap-x-8 gap-y-3 border-y border-border py-5">
        {counts.map(([s, n]) => (
          <button
            key={s}
            type="button"
            onClick={() => setFilter(filter === s ? null : s)}
            className={`text-sm ${filter && filter !== s ? "opacity-50" : ""}`}
            aria-pressed={filter === s}
          >
            <b className="mr-2 font-display text-2xl text-primary">{n}</b>
            <span className="capitalize text-muted-foreground">{s}</span>
          </button>
        ))}
      </div>
      <section className="mt-10">
        <FindingsList findings={shown} onReview={onReview} />
      </section>
    </div>
  );
}
