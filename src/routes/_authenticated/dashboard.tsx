import { createFileRoute, Link } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import {
  AlertOctagon,
  ArrowRight,
  BookOpenCheck,
  FileSearch,
  FileSpreadsheet,
  Files,
  Gauge,
  Landmark,
  Layers,
  PackageCheck,
  Search,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import {
  ActivityChart,
  AlertsFeed,
  CategoryBars,
  CompactFindingList,
  DomainCoverage,
  FindingsDonut,
  KpiTile,
  Panel,
  PriorityQueue,
  RankedList,
  ReadinessGauge,
  StandardsNetwork,
  TopStandards,
} from "@/components/dashboard/widgets";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import type { DocumentAnalysis, DocumentTypeKey } from "@/lib/contracts";
import { buildInsights, inr, istDate, istGreeting } from "@/lib/dashboard-insights";
import {
  formatAnalyzedAt,
  getChangeImpact,
  getCorpusStatus,
  listDocuments,
} from "@/services/analysis";

export const Route = createFileRoute("/_authenticated/dashboard")({
  loader: async () => {
    const [documents, events, corpus] = await Promise.all([
      listDocuments(),
      getChangeImpact().catch(() => []),
      getCorpusStatus().catch(() => null),
    ]);
    return { documents, events, corpus };
  },
  head: () => ({
    meta: [
      { title: "Workspace Overview — STANDARDOS" },
      {
        name: "description",
        content:
          "Procurement specification readiness, IS standards coverage and compliance actions.",
      },
    ],
  }),
  component: Dashboard,
});

const QUICK_ACTIONS: Array<{
  title: string;
  text: string;
  icon: LucideIcon;
  type?: DocumentTypeKey;
  to?: "/search";
}> = [
  {
    title: "Analyse a tender / NIT",
    text: "CPWD, PWD, DISCOM, JJM…",
    icon: Landmark,
    type: "tender",
  },
  { title: "Check a BOQ", text: "Schedule of quantities", icon: FileSpreadsheet, type: "boq" },
  {
    title: "Verify a vendor datasheet",
    text: "GTP against IS limits",
    icon: PackageCheck,
    type: "datasheet",
  },
  { title: "Look up an IS standard", text: "Clause-level search", icon: Search, to: "/search" },
];

function Dashboard() {
  const { documents, events, corpus } = Route.useLoaderData();
  const { profile, isDemo } = useAuth();
  const insights = buildInsights(documents, corpus, events);
  const first = profile?.full_name.split(" ")[0] ?? "there";
  const now = new Date();
  const hasData = insights.analysed.length > 0;

  return (
    <div className="reveal space-y-6">
      {/* ---------- Header ---------- */}
      <header className="intel-card overflow-hidden p-0">
        <div className="relative grid gap-6 p-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-y-0 left-0 w-1.5"
            style={{
              background:
                "linear-gradient(180deg, var(--chart-saffron) 0 33%, var(--card) 33% 66%, var(--chart-verified) 66% 100%)",
            }}
          />
          <div className="min-w-0 pl-2">
            <p className="eyebrow">
              {istDate(now, { weekday: "long", day: "numeric", month: "long", year: "numeric" })} ·
              IST{isDemo ? " · Demo workspace" : ""}
            </p>
            <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-primary sm:text-4xl">
              {istGreeting(now)}, {first}
              <span className="ml-3 align-middle text-lg font-semibold text-muted-foreground">
                नमस्ते
              </span>
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              {profile?.organization ? (
                <b className="text-primary">{profile.organization}</b>
              ) : (
                "Your workspace"
              )}{" "}
              —{" "}
              {hasData
                ? `${inr(insights.analysed.length)} documents analysed against ${inr(
                    insights.standardsReferenced,
                  )} Indian Standards; ${inr(insights.openFindings)} findings await review.`
                : "analyse your first tender to see readiness, IS coverage and compliance actions here."}
            </p>
            <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
              {corpus && (
                <Link
                  to="/admin"
                  className="rounded-full border border-border bg-background/70 px-2.5 py-1 font-semibold text-primary hover:bg-accent/30"
                >
                  BIS corpus {corpus.version} · {corpus.standards.length} standards ·{" "}
                  {inr(corpus.clauses)} clauses
                </Link>
              )}
              {insights.processing > 0 && (
                <span className="rounded-full bg-accent/40 px-2.5 py-1 font-semibold text-accent-foreground">
                  {insights.processing} analysis running
                </span>
              )}
              {insights.failed > 0 && (
                <Link
                  to="/documents"
                  className="rounded-full bg-destructive/10 px-2.5 py-1 font-semibold text-destructive"
                >
                  {insights.failed} failed — retry from Documents
                </Link>
              )}
            </div>
          </div>
          <Button asChild size="lg" className="gap-2 self-start lg:self-end">
            <Link to="/analyze">
              <FileSearch className="size-4" /> New analysis
            </Link>
          </Button>
        </div>
        <nav
          aria-label="Quick actions"
          className="grid grid-cols-2 border-t border-border/60 bg-background/40 lg:grid-cols-4"
        >
          {QUICK_ACTIONS.map((a) => {
            const body = (
              <>
                <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-primary/8 text-accent-foreground ring-1 ring-border">
                  <a.icon className="size-4" />
                </span>
                <span className="min-w-0">
                  <b className="block truncate text-sm text-primary">{a.title}</b>
                  <span className="block truncate text-[11px] text-muted-foreground">{a.text}</span>
                </span>
              </>
            );
            const cls =
              "flex items-center gap-3 border-border/60 p-4 transition hover:bg-accent/25 [&:not(:last-child)]:border-r max-lg:[&:nth-child(2)]:border-r-0 max-lg:[&:nth-child(-n+2)]:border-b";
            return a.to ? (
              <Link key={a.title} to={a.to} className={cls}>
                {body}
              </Link>
            ) : (
              <Link
                key={a.title}
                to="/analyze"
                search={a.type ? { type: a.type } : {}}
                className={cls}
              >
                {body}
              </Link>
            );
          })}
        </nav>
      </header>

      {/* ---------- KPIs ---------- */}
      <section
        className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6"
        aria-label="Key figures"
      >
        <KpiTile
          label="Documents"
          value={inr(insights.analysed.length)}
          hint={`${documents.length} in library`}
          icon={Files}
          to="/documents"
        />
        <KpiTile
          label="Requirements"
          value={inr(insights.requirements)}
          hint="extracted & classified"
          icon={Layers}
          to="/documents"
        />
        <KpiTile
          label="IS standards"
          value={inr(insights.standardsReferenced)}
          hint="referenced by your docs"
          icon={BookOpenCheck}
          to="/standards"
        />
        <KpiTile
          label="Open findings"
          value={inr(insights.openFindings)}
          hint="awaiting reviewer decision"
          icon={ShieldAlert}
          to="/compliance"
          tone={insights.openFindings ? "alert" : "good"}
        />
        <KpiTile
          label="High severity"
          value={inr(insights.highSeverity)}
          hint="fix before bid issue"
          icon={AlertOctagon}
          to="/compliance"
          tone={insights.highSeverity ? "alert" : "good"}
        />
        <KpiTile
          label="Avg. readiness"
          value={insights.averageReadiness === null ? "—" : `${insights.averageReadiness}%`}
          hint="severity-weighted score"
          icon={Gauge}
          to="/documents"
          tone={(insights.averageReadiness ?? 0) >= 80 ? "good" : "default"}
        />
      </section>

      {!hasData && <Onboarding />}

      {/* ---------- Readiness · findings · alerts ---------- */}
      <div className="grid gap-4 lg:grid-cols-12">
        <Panel
          eyebrow="Bid readiness"
          title="How ready are your specifications?"
          action={{ label: "Documents", to: "/documents" }}
          className="lg:col-span-5"
        >
          <ReadinessGauge insights={insights} />
        </Panel>
        <Panel
          eyebrow="Compliance audit"
          title="What the checks found"
          action={{ label: "Review", to: "/compliance" }}
          info="Open findings by kind, plus requirements verified against the standard."
          className="lg:col-span-4"
        >
          <FindingsDonut insights={insights} />
        </Panel>
        <Panel
          eyebrow="Standards watch"
          title="IS amendments & revisions"
          action={{ label: "Impact", to: "/changes" }}
          className="lg:col-span-3"
        >
          <AlertsFeed events={insights.alerts} />
        </Panel>
      </div>

      {/* ---------- Network ---------- */}
      <Panel
        eyebrow="Connections"
        title="Your specifications ↔ the Indian Standards they rely on"
        action={{ label: "Dependency DAG", to: "/standards" }}
        info="Each line joins a document to an IS standard its requirements map to. Colour shows whether that link has an open issue."
      >
        <StandardsNetwork insights={insights} />
      </Panel>

      {/* ---------- Actions ---------- */}
      <div className="grid gap-4 lg:grid-cols-12">
        <Panel
          eyebrow="Do this next"
          title="Priority review queue"
          action={{ label: "All findings", to: "/compliance" }}
          className="lg:col-span-5"
        >
          <PriorityQueue items={insights.priority} />
        </Panel>
        <Panel
          eyebrow="Most relied on"
          title="Top IS standards in your documents"
          action={{ label: "Catalogue", to: "/standards" }}
          className="lg:col-span-4"
        >
          <TopStandards standards={insights.standards} />
        </Panel>
        <div className="grid gap-4 lg:col-span-3">
          <Panel eyebrow="BIS conformity" title="ISI mark / certification gaps">
            <CompactFindingList
              items={insights.certification}
              empty="Every product standard has a conformity-evidence route."
            />
          </Panel>
          <Panel eyebrow="Outdated references" title="Superseded IS editions cited">
            <CompactFindingList
              items={insights.outdatedReferences}
              empty="No superseded or withdrawn IS cited."
            />
          </Panel>
        </div>
      </div>

      {/* ---------- Composition ---------- */}
      <div className="grid gap-4 lg:grid-cols-12">
        <Panel
          eyebrow="Requirement mix"
          title="What your documents ask for"
          className="lg:col-span-4"
        >
          <CategoryBars insights={insights} />
        </Panel>
        <Panel
          eyebrow="Coverage"
          title="Requirements by IS domain"
          action={{ label: "Standards", to: "/standards" }}
          className="lg:col-span-4"
        >
          <DomainCoverage insights={insights} />
        </Panel>
        <Panel eyebrow="Workload" title="Activity & sources" className="lg:col-span-4">
          <ActivityChart insights={insights} />
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            <div>
              <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.12em] text-muted-foreground">
                Document types
              </p>
              <RankedList items={insights.documentTypes.slice(0, 4)} unit="docs" />
            </div>
            <div>
              <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.12em] text-muted-foreground">
                Needs most attention
              </p>
              <RankedList
                items={[...insights.analysed]
                  .filter((d) => d.issues > 0)
                  .sort((a, b) => b.issues - a.issues)
                  .slice(0, 4)
                  .map((d) => ({ name: d.name, count: d.issues, note: `${d.readiness}%` }))}
                unit="issues"
              />
            </div>
          </div>
        </Panel>
      </div>

      {/* ---------- Recent ---------- */}
      <Panel
        eyebrow="Library"
        title="Recent analyses"
        action={{ label: "All documents", to: "/documents" }}
      >
        <RecentTable documents={documents} />
      </Panel>
    </div>
  );
}

function Onboarding() {
  const steps = [
    {
      title: "Upload a tender, BOQ or datasheet",
      text: "PDF, DOCX or pasted text — Hindi header lines are fine.",
      to: "/analyze" as const,
    },
    {
      title: "Review the findings",
      text: "Confirm or dismiss each conflict and gap; every decision is audited.",
      to: "/compliance" as const,
    },
    {
      title: "Apply the repairs",
      text: "Accept suggested clause wording and export the compliance report.",
      to: "/documents" as const,
    },
  ];
  return (
    <section className="intel-card grid gap-4 p-5 md:grid-cols-[auto_minmax(0,1fr)] md:items-center">
      <span className="grid size-12 place-items-center rounded-xl bg-accent/40 text-accent-foreground">
        <Sparkles className="size-6" />
      </span>
      <ol className="grid gap-3 md:grid-cols-3">
        {steps.map((s, i) => (
          <li key={s.title}>
            <Link
              to={s.to}
              className="block rounded-lg border border-border/60 p-3 hover:bg-accent/20"
            >
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Step {i + 1}
              </span>
              <b className="block text-sm text-primary">{s.title}</b>
              <span className="text-[11px] text-muted-foreground">{s.text}</span>
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}

function RecentTable({ documents }: { documents: DocumentAnalysis[] }) {
  if (!documents.length)
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No documents yet.{" "}
        <Link to="/analyze" className="font-bold text-accent-foreground hover:underline">
          Analyse your first tender
        </Link>
      </p>
    );
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b border-border/60 text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">
            <th className="py-2.5 pr-4">Document</th>
            <th className="px-3 py-2.5">Type</th>
            <th className="px-3 py-2.5">Status</th>
            <th className="px-3 py-2.5 text-right">IS</th>
            <th className="px-3 py-2.5 text-right">Issues</th>
            <th className="px-3 py-2.5">Readiness</th>
            <th className="py-2.5 pl-3 text-right">Analysed</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/50">
          {documents.slice(0, 8).map((doc) => {
            const ready = doc.runStatus === "succeeded";
            const color =
              doc.readiness >= 80
                ? "var(--chart-verified)"
                : doc.readiness >= 50
                  ? "var(--chart-gap)"
                  : "var(--chart-conflict)";
            return (
              <tr key={doc.id} className="hover:bg-accent/15">
                <td className="max-w-xs py-3 pr-4">
                  <Link
                    to="/documents/$documentId"
                    params={{ documentId: doc.id }}
                    className="block truncate font-bold text-primary hover:text-accent-foreground"
                  >
                    {doc.name}
                  </Link>
                  <span className="block truncate text-[11px] text-muted-foreground">
                    {doc.organization}
                  </span>
                </td>
                <td className="px-3 py-3 text-xs">
                  <span className="rounded-md border border-border/70 bg-background/60 px-1.5 py-0.5">
                    {doc.documentTypeLabel}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span
                    className={
                      "rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider " +
                      (doc.status === "Analyzed"
                        ? "bg-success/25 text-success-foreground"
                        : doc.status === "Failed"
                          ? "bg-destructive/15 text-destructive"
                          : "bg-warning/25 text-warning-foreground")
                    }
                  >
                    {doc.status}
                  </span>
                </td>
                <td className="px-3 py-3 text-right font-mono text-xs">{doc.standards}</td>
                <td className="px-3 py-3 text-right font-mono text-xs font-bold">{doc.issues}</td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${ready ? doc.readiness : 0}%`, background: color }}
                      />
                    </div>
                    <span className="font-mono text-xs font-bold">
                      {ready ? `${doc.readiness}%` : "—"}
                    </span>
                  </div>
                </td>
                <td className="py-3 pl-3 text-right text-xs text-muted-foreground">
                  {formatAnalyzedAt(doc.analyzedAt)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {documents.length > 8 && (
        <Link
          to="/documents"
          className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-accent-foreground"
        >
          {inr(documents.length - 8)} more <ArrowRight className="size-3" />
        </Link>
      )}
    </div>
  );
}
