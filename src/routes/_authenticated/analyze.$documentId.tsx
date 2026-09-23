import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Download,
  WandSparkles,
} from "lucide-react";
import { RelationshipGraph } from "@/components/analysis/relationship-graph";
import { FindingsList } from "@/components/analysis/findings";
import { RepairPanel } from "@/components/analysis/repair-panel";
import { useReviewActions } from "@/components/analysis/use-review";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { downloadComplianceReport, formatAnalyzedAt, getAnalysis } from "@/services/analysis";

export const Route = createFileRoute("/_authenticated/analyze/$documentId")({
  loader: async ({ params }) => {
    const document = await getAnalysis(params.documentId);
    if (!document) throw notFound();
    return document;
  },
  head: ({ loaderData }) => ({
    meta: [
      { title: `${loaderData?.name ?? "Analysis"} — STANDARDOS` },
      { name: "description", content: "Evidence-backed standards and compliance analysis." },
      { property: "og:title", content: "Specification Analysis — STANDARDOS" },
      { property: "og:description", content: "Review standards, conflicts, and repairs." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Results,
});

function Results() {
  const doc = Route.useLoaderData();
  const { onReview, onDecide } = useReviewActions([doc]);
  const failed = doc.runStatus === "failed";
  return (
    <div className="reveal">
      <Link
        to="/analyze"
        className="mb-7 flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-primary"
      >
        <ArrowLeft className="size-4" />
        New analysis
      </Link>
      <header>
        <p className="eyebrow">
          {failed
            ? "Analysis failed"
            : doc.runStatus === "succeeded"
              ? "Analysis complete"
              : "Analysis in progress"}{" "}
          · {formatAnalyzedAt(doc.analyzedAt)}
          {doc.isSample ? " · Sample document" : ""}
        </p>
        <h1 className="mt-3 font-display text-4xl text-primary sm:text-5xl">{doc.name}</h1>
        {failed && (
          <p role="alert" className="mt-6 flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="size-4" />
            {doc.runError ?? "The analysis failed."}
          </p>
        )}
        {doc.warnings.length > 0 && (
          <ul className="mt-6 grid gap-1 border-l-2 border-warning-foreground pl-4 text-sm text-muted-foreground">
            {doc.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        )}
        <div className="mt-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-bold text-primary">Specification Readiness</p>
            <p
              className="mt-1 text-xs text-muted-foreground"
              title={doc.readinessFormula ?? undefined}
            >
              Mapping coverage less a severity-weighted penalty for open findings
            </p>
          </div>
          <p className="font-display text-4xl text-primary">{doc.readiness}%</p>
        </div>
        <div className="mt-3 h-2 overflow-hidden bg-secondary">
          <div className="h-full bg-accent-foreground" style={{ width: `${doc.readiness}%` }} />
        </div>
        <div className="mt-8 grid grid-cols-2 border-y border-border md:grid-cols-4">
          {[
            [String(doc.requirementCount), "Requirements detected"],
            [String(doc.standards), "Standards identified"],
            [String(doc.certificationCount), "Certifications"],
            [String(doc.issues), "Issues requiring review"],
          ].map(([v, l], i) => (
            <div key={l} className={`py-5 ${i > 0 ? "md:border-l md:pl-6" : ""}`}>
              <p className="font-display text-3xl text-primary">{v}</p>
              <p className="mt-1 text-xs text-muted-foreground">{l}</p>
            </div>
          ))}
        </div>
      </header>
      <Tabs defaultValue="graph" className="mt-12">
        <TabsList className="flex h-auto flex-wrap justify-start">
          <TabsTrigger value="graph">Requirement graph</TabsTrigger>
          <TabsTrigger value="audit">Compliance audit</TabsTrigger>
          <TabsTrigger value="repair">Specification repair</TabsTrigger>
        </TabsList>
        <TabsContent value="graph" className="mt-8">
          <Section
            title="Requirement relationship"
            eyebrow="Evidence graph"
            description="Follow the selected procurement requirement through its standard, normative clause, test method, and certification."
          >
            <RelationshipGraph paths={doc.graphPaths} />
          </Section>
        </TabsContent>
        <TabsContent value="audit" className="mt-8">
          <Section
            title="Compliance audit"
            eyebrow="Actionable findings"
            description="Open any finding to review its source, governing evidence, severity, and recommended response. Confirm or dismiss it to record your decision."
          >
            <FindingsList findings={doc.findings} onReview={onReview} />
          </Section>
        </TabsContent>
        <TabsContent value="repair" className="mt-8">
          <Section
            title="Repair Specification"
            eyebrow="Evidence-backed corrections"
            description="Review each generated correction. Accept, reject, or edit the proposed requirement before export."
          >
            {doc.repairs.length ? (
              <RepairPanel repairs={doc.repairs} onDecide={onDecide} />
            ) : (
              <div className="py-14 text-center">
                <CheckCircle2 className="mx-auto size-8 text-success-foreground" />
                <p className="mt-4 font-bold text-primary">No repairs are required.</p>
              </div>
            )}
          </Section>
        </TabsContent>
      </Tabs>
      <div className="mt-12 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-xl text-xs leading-5 text-muted-foreground">
          Pipeline {doc.pipelineVersion ?? "—"} · standards corpus {doc.corpusVersion ?? "—"}
          {doc.corpusSource ? ` (${doc.corpusSource})` : ""}. Decision support only: findings and
          repairs must be reviewed by qualified personnel.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => void downloadComplianceReport(doc)}>
            <Download />
            Compliance report
          </Button>
          <Button asChild>
            <Link to="/documents">
              <WandSparkles />
              Return to document library <ArrowRight />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function Section({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="section-title mt-2">{title}</h2>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">{description}</p>
      <div className="mt-7">{children}</div>
    </section>
  );
}
