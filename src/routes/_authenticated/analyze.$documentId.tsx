import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock,
  Download,
  FileCheck2,
  GitBranch,
  Layers,
  ShieldAlert,
  ShieldCheck,
  Wand2,
} from "lucide-react";
import { useState } from "react";
import { RelationshipGraph } from "@/components/analysis/relationship-graph";
import { FindingsList } from "@/components/analysis/findings";
import { RepairPanel } from "@/components/analysis/repair-panel";
import { useReviewActions } from "@/components/analysis/use-review";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { downloadComplianceReport, formatAnalyzedAt, getAnalysis } from "@/services/analysis";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { EvidenceDrawer } from "@/components/shared/evidence-drawer";
import type { Requirement } from "@/lib/contracts";

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
  const [selectedReq, setSelectedReq] = useState<Requirement | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const failed = doc.runStatus === "failed";
  const conflictsCount = doc.findings.filter((f) => f.status === "conflicting").length;

  return (
    <div className="reveal space-y-8">
      {/* Back button & Eyebrow */}
      <div className="flex items-center justify-between">
        <Link
          to="/analyze"
          className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-primary transition"
        >
          <ArrowLeft className="size-3.5" />
          <span>Start Another Analysis</span>
        </Link>
        <span className="font-mono text-xs text-muted-foreground">
          {formatAnalyzedAt(doc.analyzedAt)}
          {doc.isSample ? " · Sample Document" : ""}
        </span>
      </div>

      {/* Main Header */}
      <PageHeader
        eyebrow={`${doc.documentTypeLabel} · ${doc.type} · ${doc.organization}`}
        title={doc.name}
        description={`Analyzed against Indian Standards corpus ${doc.corpusVersion ?? "3.1"}. Review extracted requirements, normative graph linkages, and evidence-backed corrections.`}
      >
        <Button
          variant="outline"
          size="sm"
          onClick={() => void downloadComplianceReport(doc)}
          className="gap-2"
        >
          <Download className="size-4" />
          <span>Export Report</span>
        </Button>
        <Button asChild size="sm" className="gap-2">
          <Link to="/documents">
            <span>Documents Library</span>
            <ArrowRight className="size-4" />
          </Link>
        </Button>
      </PageHeader>

      {/* Errors / Warnings */}
      {failed && (
        <div
          role="alert"
          className="flex items-center gap-2.5 rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm font-semibold text-destructive"
        >
          <AlertCircle className="size-5 shrink-0" />
          <span>{doc.runError ?? "The analysis pipeline failed to complete."}</span>
        </div>
      )}

      {doc.warnings.length > 0 && (
        <div className="rounded-xl border border-warning/40 bg-warning/10 p-4 text-xs text-warning-foreground space-y-1">
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-[11px]">
            <AlertTriangle className="size-4" />
            <span>Analysis Advisories</span>
          </div>
          <ul className="list-disc pl-5 space-y-0.5">
            {doc.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Executive Metric Cards */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label="Specification Readiness"
          value={`${doc.readiness}%`}
          icon={ShieldCheck}
          subtitle="Mapping coverage less issue penalties"
          trend={{
            value: doc.readiness >= 80 ? "Pass readiness" : "Review required",
            positive: doc.readiness >= 80,
          }}
        />
        <MetricCard
          label="Mapped Standards"
          value={doc.standards}
          icon={BookOpen}
          subtitle="Indian Standards identified"
          trend={{ value: `${doc.certificationCount} mandatory certs`, neutral: true }}
        />
        <MetricCard
          label="Extracted Requirements"
          value={doc.requirementCount || doc.requirements.length}
          icon={Layers}
          subtitle="Governing obligations"
          trend={{ value: "Indexed in Graph", neutral: true }}
        />
        <MetricCard
          label="Compliance Findings"
          value={doc.issues}
          icon={ShieldAlert}
          subtitle={`${conflictsCount} critical conflicts`}
          trend={{
            value: doc.issues === 0 ? "Zero flags" : `${doc.repairs.length} corrections available`,
            positive: doc.issues === 0,
          }}
        />
      </section>

      {/* Analysis Workbench Tabs */}
      <Tabs defaultValue="audit" className="space-y-6">
        <div className="border-b border-border/70 pb-1">
          <TabsList className="flex flex-wrap h-auto gap-2 bg-transparent p-0">
            <TabsTrigger
              value="audit"
              className="gap-2 rounded-lg border border-border/70 bg-card/60 px-4 py-2.5 text-xs font-bold data-[state=active]:border-accent-foreground data-[state=active]:bg-accent/30 data-[state=active]:text-primary"
            >
              <FileCheck2 className="size-4 text-accent-foreground" />
              <span>Compliance Audit</span>
              <span className="rounded-full bg-accent/40 px-2 py-0.5 font-mono text-[10px]">
                {doc.findings.length}
              </span>
            </TabsTrigger>

            <TabsTrigger
              value="graph"
              className="gap-2 rounded-lg border border-border/70 bg-card/60 px-4 py-2.5 text-xs font-bold data-[state=active]:border-accent-foreground data-[state=active]:bg-accent/30 data-[state=active]:text-primary"
            >
              <GitBranch className="size-4 text-accent-foreground" />
              <span>Evidence Graph</span>
              <span className="rounded-full bg-accent/40 px-2 py-0.5 font-mono text-[10px]">
                {doc.graphPaths.length}
              </span>
            </TabsTrigger>

            <TabsTrigger
              value="repair"
              className="gap-2 rounded-lg border border-border/70 bg-card/60 px-4 py-2.5 text-xs font-bold data-[state=active]:border-accent-foreground data-[state=active]:bg-accent/30 data-[state=active]:text-primary"
            >
              <Wand2 className="size-4 text-accent-foreground" />
              <span>Specification Repair</span>
              <span className="rounded-full bg-accent/40 px-2 py-0.5 font-mono text-[10px]">
                {doc.repairs.length}
              </span>
            </TabsTrigger>

            <TabsTrigger
              value="requirements"
              className="gap-2 rounded-lg border border-border/70 bg-card/60 px-4 py-2.5 text-xs font-bold data-[state=active]:border-accent-foreground data-[state=active]:bg-accent/30 data-[state=active]:text-primary"
            >
              <Layers className="size-4 text-accent-foreground" />
              <span>Requirements</span>
              <span className="rounded-full bg-accent/40 px-2 py-0.5 font-mono text-[10px]">
                {doc.requirements.length}
              </span>
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab 1: Compliance Audit */}
        <TabsContent value="audit" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="eyebrow">Actionable Audit Flags</p>
              <h2 className="text-xl font-bold text-primary">Compliance Findings</h2>
            </div>
            <span className="text-xs text-muted-foreground">
              Review flagged evidence, confirm decisions, or dismiss as not applicable
            </span>
          </div>
          <FindingsList findings={doc.findings} onReview={onReview} />
        </TabsContent>

        {/* Tab 2: Evidence Graph */}
        <TabsContent value="graph" className="space-y-4">
          <div>
            <p className="eyebrow">Topological Evidence Mapping</p>
            <h2 className="text-xl font-bold text-primary">Requirement Relationship Trail</h2>
            <p className="text-xs text-muted-foreground mt-1">
              Trace requirements from specification text through governing standard, clause,
              normative test method, and mandatory certification.
            </p>
          </div>
          <RelationshipGraph paths={doc.graphPaths} />
        </TabsContent>

        {/* Tab 3: Specification Repair */}
        <TabsContent value="repair" className="space-y-4">
          <div>
            <p className="eyebrow">Evidence-Led Corrections</p>
            <h2 className="text-xl font-bold text-primary">Specification Repair Workbench</h2>
            <p className="text-xs text-muted-foreground mt-1">
              Review recommended phrasing updates to bring clauses into conformance with governing
              Indian Standards.
            </p>
          </div>
          {doc.repairs.length ? (
            <RepairPanel repairs={doc.repairs} onDecide={onDecide} />
          ) : (
            <div className="intel-card py-16 text-center space-y-3">
              <CheckCircle2 className="mx-auto size-10 text-success-foreground" />
              <h3 className="text-base font-bold text-primary">Zero repairs needed</h3>
              <p className="text-xs text-muted-foreground max-w-md mx-auto">
                No contradictory or outdated requirements were identified in this specification.
              </p>
            </div>
          )}
        </TabsContent>

        {/* Tab 4: Requirements Catalog */}
        <TabsContent value="requirements" className="space-y-4">
          <div>
            <p className="eyebrow">Extracted Corpus</p>
            <h2 className="text-xl font-bold text-primary">Document Requirements</h2>
            <p className="text-xs text-muted-foreground mt-1">
              Click any requirement row to inspect full clause details, provenance, and governing
              standard.
            </p>
          </div>
          <div className="intel-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[700px] text-left text-sm">
                <thead>
                  <tr className="border-b border-border/70 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                    <th className="py-3 px-4">Requirement</th>
                    <th className="py-3 px-3">Category</th>
                    <th className="py-3 px-3">Standard</th>
                    <th className="py-3 px-3">Governing Clause</th>
                    <th className="py-3 px-3 text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {doc.requirements.map((req) => (
                    <tr
                      key={req.id}
                      className="group transition-colors hover:bg-accent/20 cursor-pointer"
                      onClick={() => {
                        setSelectedReq(req);
                        setDrawerOpen(true);
                      }}
                    >
                      <td className="py-3 px-4 max-w-md">
                        <p className="font-semibold text-primary truncate">{req.text}</p>
                        {req.sectionLabel && (
                          <span className="text-[10px] text-muted-foreground">
                            {req.sectionLabel}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-xs text-muted-foreground font-medium">
                        {req.category}
                      </td>
                      <td className="py-3 px-3 font-mono text-xs font-bold text-accent-foreground">
                        {req.standard}
                      </td>
                      <td className="py-3 px-3 text-xs text-muted-foreground">
                        {req.clause || "—"}
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-xs font-bold text-primary">
                        {req.confidence !== undefined
                          ? `${Math.round(req.confidence * 100)}%`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Requirement Details Drawer */}
      <EvidenceDrawer requirement={selectedReq} open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
