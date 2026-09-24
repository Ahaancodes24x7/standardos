import { createFileRoute, Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  FileSearch,
  FileText,
  Files,
  Layers,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { workspaceStats } from "@/lib/analysis-view";
import { formatAnalyzedAt, listDocuments } from "@/services/analysis";
import { MetricCard } from "@/components/shared/metric-card";
import { StatusBadge } from "@/components/shared/status-badge";
import { PageHeader } from "@/components/shared/page-header";

export const Route = createFileRoute("/_authenticated/dashboard")({
  loader: () => listDocuments(),
  head: () => ({
    meta: [
      { title: "Workspace Overview — STANDARDOS" },
      {
        name: "description",
        content: "Procurement specification readiness and recent compliance intelligence.",
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

  // Compute workspace aggregate data
  const totalRequirements = documents.reduce(
    (sum, d) => sum + (d.requirementCount ?? d.requirements?.length ?? 0),
    0,
  );
  const allFindings = documents.flatMap((d) => d.findings ?? []);
  const totalFindings = allFindings.length;
  // "Flagged" = needs attention; verified matches are shown separately in the breakdown.
  const openFindings = allFindings.filter((f) => f.status !== "verified").length;

  const conflictsCount = allFindings.filter((f) => f.status === "conflicting").length;
  const gapsCount = allFindings.filter((f) => f.status === "missing").length;
  const outdatedCount = allFindings.filter((f) => f.status === "outdated").length;
  const certCount = allFindings.filter((f) => f.status === "certification").length;
  const verifiedCount = allFindings.filter((f) => f.status === "verified").length;

  // Chart data 1: Findings breakdown
  const findingBreakdownData = [
    { name: "Conflicts", count: conflictsCount, fill: "var(--destructive)" },
    { name: "Gaps / Missing", count: gapsCount, fill: "var(--warning)" },
    {
      name: "Outdated",
      count: outdatedCount,
      fill: "color-mix(in oklab, var(--warning) 80%, black)",
    },
    { name: "Certification", count: certCount, fill: "var(--accent-foreground)" },
    { name: "Verified", count: verifiedCount, fill: "var(--success)" },
  ];

  // Chart data 2: Readiness index trend across recent documents
  const readinessTrendData = [...documents]
    .slice(0, 7)
    .reverse()
    .map((doc, idx) => ({
      name: doc.name.length > 14 ? `${doc.name.slice(0, 12)}…` : doc.name,
      readiness: doc.runStatus === "succeeded" ? doc.readiness : 0,
      standards: doc.standards,
      issues: doc.issues,
    }));

  return (
    <div className="reveal space-y-8">
      {/* Page Header */}
      <PageHeader
        eyebrow={`Workspace Overview${isDemo ? " · Demonstration Account" : ""}`}
        title={`${greeting}, ${first}.`}
        description="Real-time compliance readiness, standards mapping, and actionable findings across your specifications."
      >
        <Button asChild size="lg" className="gap-2 shadow-xs">
          <Link to="/analyze">
            <FileSearch className="size-4" />
            <span>Analyze New Specification</span>
          </Link>
        </Button>
      </PageHeader>

      {/* KPI Metric Strip */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Documents Analyzed"
          value={stats.documents}
          icon={Files}
          subtitle={`${stats.standardsMapped} standards mapped`}
          trend={{ value: `${documents.length} active in workspace`, neutral: true }}
        />
        <MetricCard
          label="Extracted Requirements"
          value={totalRequirements}
          icon={Layers}
          subtitle="Governing clause linkages"
          trend={{ value: "Indexed in Graph", neutral: true }}
        />
        <MetricCard
          label="Findings Flagged"
          value={openFindings}
          icon={ShieldAlert}
          subtitle={`${conflictsCount} conflicts · ${gapsCount} gaps`}
          trend={{
            value:
              stats.requireAttention > 0
                ? `${stats.requireAttention} docs need review`
                : "All clear",
            positive: stats.requireAttention === 0,
          }}
        />
        <MetricCard
          label="Average Readiness"
          value={stats.averageReadiness === null ? "—" : `${stats.averageReadiness}%`}
          icon={ShieldCheck}
          subtitle="Severity-weighted compliance score"
          trend={{
            value: (stats.averageReadiness ?? 0) >= 80 ? "High compliance" : "Review advised",
            positive: (stats.averageReadiness ?? 0) >= 80,
          }}
        />
      </section>

      {/* Visual Analytics Row */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Compliance Readiness Chart */}
        <div className="intel-card p-5 lg:col-span-7">
          <div className="flex items-center justify-between border-b border-border/70 pb-3">
            <div>
              <p className="eyebrow">Specification Readiness</p>
              <h2 className="text-base font-bold text-primary">Readiness by Specification (%)</h2>
            </div>
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold">
              <TrendingUp className="size-3.5 text-accent-foreground" />
              <span>Recent runs</span>
            </span>
          </div>

          <div className="mt-4 h-64 w-full">
            {readinessTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={readinessTrendData}
                  margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="color-mix(in oklab, var(--border) 60%, transparent)"
                  />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                    interval={0}
                    angle={-15}
                    textAnchor="end"
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      const data = active ? payload?.[0]?.payload : undefined;
                      if (!data) return null;
                      return (
                        <div className="rounded-lg border border-border bg-popover p-3 text-xs shadow-lg">
                          <p className="font-bold text-popover-foreground">{data.name}</p>
                          <p className="mt-1 text-primary">
                            Readiness:{" "}
                            <span className="font-mono font-bold">{data.readiness}%</span>
                          </p>
                          <p className="text-muted-foreground">
                            {data.standards} standards · {data.issues} issues
                          </p>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="readiness" radius={[4, 4, 0, 0]} fill="var(--primary)">
                    {readinessTrendData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          entry.readiness >= 80
                            ? "var(--success-foreground)"
                            : entry.readiness >= 50
                              ? "var(--warning-foreground)"
                              : "var(--destructive)"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="grid h-full place-items-center text-xs text-muted-foreground">
                No specification data available to chart.
              </div>
            )}
          </div>
        </div>

        {/* Finding Distribution Chart */}
        <div className="intel-card p-5 lg:col-span-5 flex flex-col justify-between">
          <div className="border-b border-border/70 pb-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="eyebrow">Audit Categorization</p>
                <h2 className="text-base font-bold text-primary">Findings by Severity</h2>
              </div>
              <Link
                to="/compliance"
                className="text-xs font-bold text-accent-foreground hover:underline"
              >
                View all ({totalFindings})
              </Link>
            </div>
          </div>

          <div className="mt-4 grid gap-2.5">
            {findingBreakdownData.map((item) => (
              <div
                key={item.name}
                className="flex items-center justify-between rounded-lg border border-border/60 bg-background/50 px-3.5 py-2.5 text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <span className="size-2.5 rounded-full" style={{ backgroundColor: item.fill }} />
                  <span className="font-semibold text-primary">{item.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-foreground">{item.count}</span>
                  <span className="text-[10px] text-muted-foreground">
                    ({totalFindings > 0 ? Math.round((item.count / totalFindings) * 100) : 0}%)
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 rounded-lg border border-border/70 bg-accent/20 p-3 text-xs text-muted-foreground">
            <p className="font-semibold text-primary flex items-center gap-1.5">
              <ShieldCheck className="size-3.5 text-accent-foreground" />
              <span>Evidence Traceability</span>
            </p>
            <p className="mt-0.5 text-[11px] leading-relaxed">
              Every flagged finding connects the requirement to its governing clause in the official
              Indian Standard.
            </p>
          </div>
        </div>
      </section>

      {/* Recent Specifications Table */}
      <section className="intel-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-4">
          <div>
            <p className="eyebrow">Active Specifications</p>
            <h2 className="text-xl font-bold text-primary">Recent Analyses</h2>
          </div>
          <Button asChild variant="outline" size="sm" className="gap-1.5 text-xs">
            <Link to="/documents">
              <span>View all documents</span>
              <ArrowRight className="size-3.5" />
            </Link>
          </Button>
        </div>

        <div className="mt-4 overflow-x-auto">
          {!documents.length ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No specifications analysed yet.{" "}
              <Link to="/analyze" className="font-bold text-accent-foreground hover:underline">
                Analyze your first specification
              </Link>
              .
            </div>
          ) : (
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead>
                <tr className="border-b border-border/60 text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">
                  <th className="py-3 pr-4">Specification</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Standards</th>
                  <th className="py-3 px-3">Issues</th>
                  <th className="py-3 px-3">Readiness</th>
                  <th className="py-3 pl-4 text-right">Analyzed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {documents.slice(0, 6).map((doc) => (
                  <tr
                    key={doc.id}
                    className="group transition-colors hover:bg-accent/20 cursor-pointer"
                    onClick={() => {
                      window.location.href = `/documents/${doc.id}`;
                    }}
                  >
                    <td className="py-3.5 pr-4">
                      <Link
                        to="/documents/$documentId"
                        params={{ documentId: doc.id }}
                        className="font-bold text-primary hover:text-accent-foreground block"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {doc.name}
                      </Link>
                      <span className="text-xs text-muted-foreground">
                        {doc.documentTypeLabel} · {doc.organization}
                      </span>
                    </td>
                    <td className="py-3.5 px-3">
                      <span
                        className={`inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                          doc.status === "Analyzed"
                            ? "bg-success/20 text-success-foreground"
                            : doc.status === "Failed"
                              ? "bg-destructive/20 text-destructive"
                              : "bg-warning/20 text-warning-foreground"
                        }`}
                      >
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 font-mono text-xs font-semibold text-foreground">
                      {doc.standards}
                    </td>
                    <td className="py-3.5 px-3">
                      <span
                        className={`font-mono text-xs font-bold ${
                          doc.issues > 2 ? "text-destructive" : "text-muted-foreground"
                        }`}
                      >
                        {doc.issues}
                      </span>
                    </td>
                    <td className="py-3.5 px-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-16 overflow-hidden rounded-full bg-secondary">
                          <div
                            className={`h-full ${
                              doc.readiness >= 80
                                ? "bg-success-foreground"
                                : doc.readiness >= 50
                                  ? "bg-warning-foreground"
                                  : "bg-destructive"
                            }`}
                            style={{ width: `${doc.readiness}%` }}
                          />
                        </div>
                        <span className="font-mono text-xs font-bold text-primary">
                          {doc.runStatus === "succeeded" ? `${doc.readiness}%` : "—"}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 pl-4 text-right text-xs text-muted-foreground">
                      {formatAnalyzedAt(doc.analyzedAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}
