import { Link, useNavigate } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import { ArrowRight, ArrowUpRight, BadgeCheck, CalendarClock, Info } from "lucide-react";
import { useState, type ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChangeEvent } from "@/lib/contracts";
import {
  inr,
  STATUS_META,
  type Insights,
  type PriorityItem,
  type StandardUse,
} from "@/lib/dashboard-insights";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Shells
// ---------------------------------------------------------------------------

export function Panel({
  eyebrow,
  title,
  action,
  info,
  className,
  children,
}: {
  eyebrow: string;
  title: string;
  action?: { label: string; to: string };
  info?: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section className={cn("intel-card flex min-w-0 flex-col p-5", className)}>
      <header className="flex items-start justify-between gap-3 border-b border-border/60 pb-3">
        <div className="min-w-0">
          <p className="eyebrow">{eyebrow}</p>
          <h2 className="mt-0.5 flex items-center gap-1.5 text-base font-bold text-primary">
            {title}
            {info && (
              <span title={info} className="text-muted-foreground" aria-label={info}>
                <Info className="size-3.5" />
              </span>
            )}
          </h2>
        </div>
        {action && (
          <Link
            to={action.to}
            className="flex shrink-0 items-center gap-1 text-xs font-bold text-accent-foreground hover:underline"
          >
            {action.label} <ArrowRight className="size-3" />
          </Link>
        )}
      </header>
      <div className="mt-4 min-w-0 flex-1">{children}</div>
    </section>
  );
}

export function KpiTile({
  label,
  value,
  hint,
  icon: Icon,
  to,
  tone = "default",
}: {
  label: string;
  value: string;
  hint: string;
  icon: LucideIcon;
  to: string;
  tone?: "default" | "alert" | "good";
}) {
  return (
    <Link
      to={to}
      className="intel-card intel-card-hover group flex flex-col gap-2 p-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-muted-foreground">
          {label}
        </span>
        <span
          className={cn(
            "grid size-8 place-items-center rounded-lg border",
            tone === "alert"
              ? "border-destructive/30 bg-destructive/10 text-destructive"
              : tone === "good"
                ? "border-success/40 bg-success/15 text-success-foreground"
                : "border-border/70 bg-background/70 text-accent-foreground",
          )}
        >
          <Icon className="size-4" />
        </span>
      </div>
      <span className="text-2xl font-extrabold tracking-tight text-primary tabular-nums sm:text-3xl">
        {value}
      </span>
      <span className="flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
        <span className="truncate">{hint}</span>
        <ArrowUpRight className="size-3.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-100" />
      </span>
    </Link>
  );
}

function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="grid h-full min-h-32 place-items-center rounded-lg border border-dashed border-border/70 p-4 text-center text-xs text-muted-foreground">
      {children}
    </div>
  );
}

function ChartTip({ title, lines }: { title: string; lines: string[] }) {
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 text-xs shadow-lg">
      <p className="font-bold text-popover-foreground">{title}</p>
      {lines.map((l) => (
        <p key={l} className="text-muted-foreground">
          {l}
        </p>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Readiness gauge + bands
// ---------------------------------------------------------------------------

export function ReadinessGauge({ insights }: { insights: Insights }) {
  const value = insights.averageReadiness;
  const color =
    value === null
      ? "var(--muted)"
      : value >= 80
        ? "var(--chart-verified)"
        : value >= 50
          ? "var(--chart-gap)"
          : "var(--chart-conflict)";
  const total = insights.readinessBands.reduce((s, b) => s + b.count, 0);
  return (
    <div className="grid gap-4 sm:grid-cols-[11rem_minmax(0,1fr)] sm:items-center">
      <div className="relative mx-auto size-44">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="74%"
            outerRadius="100%"
            startAngle={220}
            endAngle={-40}
            data={[{ value: value ?? 0 }]}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              dataKey="value"
              cornerRadius={10}
              background={{ fill: "var(--muted)" }}
              fill={color}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 grid place-items-center text-center">
          <div>
            <p className="text-4xl font-extrabold tracking-tight text-primary tabular-nums">
              {value === null ? "—" : `${value}%`}
            </p>
            <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-muted-foreground">
              avg. readiness
            </p>
          </div>
        </div>
      </div>
      <div className="space-y-2.5">
        {insights.readinessBands.map((b) => (
          <div key={b.key}>
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-2 font-semibold text-primary">
                <span className="size-2.5 rounded-full" style={{ background: b.color }} />
                {b.label}
                <span className="font-normal text-muted-foreground">{b.range}</span>
              </span>
              <span className="font-mono font-bold tabular-nums">{b.count}</span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${total ? (b.count / total) * 100 : 0}%`, background: b.color }}
              />
            </div>
          </div>
        ))}
        <p className="pt-1 text-[11px] leading-snug text-muted-foreground">
          Severity-weighted: each open high / medium / low finding deducts 8 / 3 / 1 points.
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Findings donut
// ---------------------------------------------------------------------------

export function FindingsDonut({ insights }: { insights: Insights }) {
  const data = insights.statusCounts.filter((s) => s.count > 0);
  const total = data.reduce((s, d) => s + d.count, 0);
  if (!total) return <Empty>No findings yet — analyse a document to populate the audit.</Empty>;
  return (
    <div className="grid gap-3 sm:grid-cols-[10rem_minmax(0,1fr)] sm:items-center">
      <div className="relative mx-auto size-40">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="label"
              innerRadius="62%"
              outerRadius="100%"
              paddingAngle={2}
              stroke="none"
            >
              {data.map((d) => (
                <Cell key={d.status} fill={d.color} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                const p = active ? payload?.[0]?.payload : undefined;
                return p ? <ChartTip title={p.label} lines={[`${inr(p.count)} findings`]} /> : null;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
          <div>
            <p className="text-2xl font-extrabold text-primary tabular-nums">{inr(total)}</p>
            <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              checks
            </p>
          </div>
        </div>
      </div>
      <ul className="space-y-1.5">
        {insights.statusCounts.map((s) => (
          <li key={s.status}>
            <Link
              to="/compliance"
              className="flex items-center justify-between rounded-md px-2 py-1.5 text-xs hover:bg-accent/30"
            >
              <span className="flex items-center gap-2 font-semibold text-primary">
                <span className="size-2.5 rounded-sm" style={{ background: s.color }} />
                {s.label}
              </span>
              <span className="font-mono tabular-nums">
                <b>{inr(s.count)}</b>
                <span className="ml-1.5 text-[10px] text-muted-foreground">
                  {total ? Math.round((s.count / total) * 100) : 0}%
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Requirement categories and IS domains
// ---------------------------------------------------------------------------

const CATEGORY_LABEL: Record<string, string> = {
  electrical: "Electrical",
  environmental: "Environmental",
  safety: "Safety",
  testing: "Testing",
  certification: "Certification",
  documentation: "Documentation",
  material: "Material",
  performance: "Performance",
  installation: "Installation",
  general: "General",
  mechanical: "Mechanical",
  dimensional: "Dimensional",
};

export function CategoryBars({ insights }: { insights: Insights }) {
  const data = insights.categories.slice(0, 8).map((c) => ({
    name: CATEGORY_LABEL[c.name] ?? c.name,
    count: c.count,
  }));
  if (!data.length) return <Empty>Requirement categories appear after the first analysis.</Empty>;
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="name"
            width={96}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
          />
          <Tooltip
            cursor={{ fill: "color-mix(in oklab, var(--accent) 25%, transparent)" }}
            content={({ active, payload }) => {
              const p = active ? payload?.[0]?.payload : undefined;
              return p ? (
                <ChartTip title={p.name} lines={[`${inr(p.count)} requirements`]} />
              ) : null;
            }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]} fill="var(--chart-primary)" barSize={14} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DomainCoverage({ insights }: { insights: Insights }) {
  const max = Math.max(1, ...insights.domains.map((d) => d.requirements));
  if (!insights.domains.length) return <Empty>No IS mappings yet.</Empty>;
  return (
    <ul className="space-y-3">
      {insights.domains.slice(0, 6).map((d) => (
        <li key={d.name}>
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-primary">{d.name}</span>
            <span className="text-muted-foreground">
              <b className="font-mono text-foreground">{inr(d.requirements)}</b> req · {d.standards}{" "}
              IS
            </span>
          </div>
          <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full"
              style={{
                width: `${(d.requirements / max) * 100}%`,
                background: "linear-gradient(90deg, var(--chart-accent), var(--chart-primary))",
              }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// Specification ↔ IS standard network
// ---------------------------------------------------------------------------

const TONE = {
  ok: "var(--chart-verified)",
  gap: "var(--chart-gap)",
  conflict: "var(--chart-conflict)",
} as const;

export function StandardsNetwork({ insights }: { insights: Insights }) {
  const navigate = useNavigate();
  const [hover, setHover] = useState<string | null>(null);
  const { documents, standards, edges } = insights.network;
  const rows = Math.max(documents.length, standards.length);
  const rowH = 46;
  const height = Math.max(160, rows * rowH + 24);
  const W = 860;
  const lx = 230;
  const rx = W - 230;
  const y = (i: number, n: number) => 12 + (height - 24) * ((i + 0.5) / n);
  const docY = new Map(documents.map((d, i) => [d.id, y(i, documents.length)]));
  const stdY = new Map(standards.map((s, i) => [s.id, y(i, standards.length)]));

  if (!edges.length) {
    return (
      <Empty>Analyse a document to see how your specifications connect to Indian Standards.</Empty>
    );
  }
  const active = (e: { doc: string; standard: string }) =>
    !hover || hover === e.doc || hover === e.standard;
  const trim = (t: string, n: number) => (t.length > n ? `${t.slice(0, n - 1)}…` : t);

  return (
    <div>
      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${height}`}
          className="h-auto w-full min-w-[640px]"
          role="img"
          aria-label="Network linking analysed specifications to the Indian Standards their requirements map to"
        >
          {edges.map((e) => {
            const y1 = docY.get(e.doc) ?? 0;
            const y2 = stdY.get(e.standard) ?? 0;
            const mid = (lx + rx) / 2;
            return (
              <path
                key={`${e.doc}-${e.standard}`}
                d={`M ${lx + 8} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${rx - 8} ${y2}`}
                fill="none"
                stroke={TONE[e.tone]}
                strokeWidth={Math.min(7, 1.2 + e.weight * 0.9)}
                strokeLinecap="round"
                opacity={active(e) ? 0.75 : 0.08}
                style={{ transition: "opacity 150ms" }}
              >
                <title>{`${e.weight} requirement(s)`}</title>
              </path>
            );
          })}
          {documents.map((d) => {
            const cy = docY.get(d.id) ?? 0;
            return (
              <g
                key={d.id}
                className="cursor-pointer"
                onMouseEnter={() => setHover(d.id)}
                onMouseLeave={() => setHover(null)}
                onClick={() =>
                  void navigate({ to: "/documents/$documentId", params: { documentId: d.id } })
                }
              >
                <circle cx={lx} cy={cy} r={8} fill="var(--chart-primary)" />
                <text
                  x={lx - 16}
                  y={cy - 2}
                  textAnchor="end"
                  fontSize={13}
                  fontWeight={700}
                  fill="var(--primary)"
                >
                  {trim(d.name, 26)}
                </text>
                <text
                  x={lx - 16}
                  y={cy + 13}
                  textAnchor="end"
                  fontSize={10.5}
                  fill="var(--muted-foreground)"
                >
                  {trim(`${d.documentTypeLabel} · ${d.readiness}% ready`, 34)}
                </text>
              </g>
            );
          })}
          {standards.map((s) => {
            const cy = stdY.get(s.id) ?? 0;
            const superseded = /superseded|withdrawn/i.test(s.status);
            return (
              <g
                key={s.id}
                className="cursor-pointer"
                onMouseEnter={() => setHover(s.id)}
                onMouseLeave={() => setHover(null)}
                onClick={() => void navigate({ to: "/standard/$id", params: { id: s.id } })}
              >
                <rect
                  x={rx - 8}
                  y={cy - 8}
                  width={16}
                  height={16}
                  rx={4}
                  fill={superseded ? "var(--chart-outdated)" : "var(--chart-accent)"}
                />
                <text x={rx + 16} y={cy - 2} fontSize={13} fontWeight={700} fill="var(--primary)">
                  {trim(s.label, 24)}
                </text>
                <text x={rx + 16} y={cy + 13} fontSize={10.5} fill="var(--muted-foreground)">
                  {s.requirements} req · {s.documents} doc{s.documents === 1 ? "" : "s"}
                  {s.openFindings ? ` · ${s.openFindings} open` : ""}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-[11px] text-muted-foreground">
        <Legend color={TONE.ok} label="Mapped, no open issue" />
        <Legend color={TONE.gap} label="Open gap / outdated / BIS" />
        <Legend color={TONE.conflict} label="Conflict with the standard" />
        <Legend color="var(--chart-outdated)" label="Superseded IS" square />
        <span className="ml-auto">
          Line width = requirements mapped · hover to trace · click to open
        </span>
      </div>
    </div>
  );
}

function Legend({ color, label, square }: { color: string; label: string; square?: boolean }) {
  return (
    <span className="flex items-center gap-1.5">
      <span
        className={cn("inline-block size-2.5", square ? "rounded-sm" : "rounded-full")}
        style={{ background: color }}
      />
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Top IS standards
// ---------------------------------------------------------------------------

export function TopStandards({ standards }: { standards: StandardUse[] }) {
  if (!standards.length) return <Empty>Standards referenced by your documents appear here.</Empty>;
  const max = Math.max(...standards.map((s) => s.requirements));
  return (
    <ul className="divide-y divide-border/50">
      {standards.slice(0, 7).map((s) => {
        const superseded = /superseded|withdrawn/i.test(s.status);
        return (
          <li key={s.id}>
            <Link
              to="/standard/$id"
              params={{ id: s.id }}
              className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 py-2.5 hover:bg-accent/15"
            >
              <span className="min-w-0">
                <span className="flex items-center gap-2">
                  <b className="truncate font-mono text-sm text-primary">{s.label}</b>
                  {superseded && (
                    <span className="rounded bg-warning/25 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-warning-foreground">
                      {s.status}
                    </span>
                  )}
                </span>
                <span className="block truncate text-[11px] text-muted-foreground">
                  {s.title || s.category}
                </span>
                <span className="mt-1 block h-1 overflow-hidden rounded-full bg-muted">
                  <span
                    className="block h-full rounded-full bg-[var(--chart-primary)]"
                    style={{ width: `${(s.requirements / max) * 100}%` }}
                  />
                </span>
              </span>
              <span className="text-right text-[11px] text-muted-foreground">
                <b className="block font-mono text-sm text-foreground">{inr(s.requirements)}</b>
                req
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// Action lists
// ---------------------------------------------------------------------------

const SEV_STYLE = {
  high: "bg-destructive/12 text-destructive border-destructive/30",
  medium: "bg-warning/20 text-warning-foreground border-warning/40",
  low: "bg-muted text-muted-foreground border-border",
} as const;

export function PriorityQueue({ items }: { items: PriorityItem[] }) {
  if (!items.length)
    return (
      <Empty>
        <span className="flex items-center gap-2 text-success-foreground">
          <BadgeCheck className="size-4" /> No open findings — every document is review-clean.
        </span>
      </Empty>
    );
  return (
    <ol className="space-y-2">
      {items.map((f, i) => (
        <li key={`${f.documentId}-${f.id}`}>
          <Link
            to="/analyze/$documentId"
            params={{ documentId: f.documentId }}
            className="grid grid-cols-[1.5rem_minmax(0,1fr)_auto] items-start gap-3 rounded-lg border border-border/60 bg-background/50 p-3 transition hover:border-accent-foreground/40 hover:bg-accent/15"
          >
            <span className="grid size-6 place-items-center rounded-full bg-primary text-[11px] font-bold text-primary-foreground">
              {i + 1}
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-bold text-primary">{f.title}</span>
              <span className="block truncate text-[11px] text-muted-foreground">
                {f.standard} · {f.documentName}
              </span>
            </span>
            <span className="flex flex-col items-end gap-1">
              <span
                className={cn(
                  "rounded border px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                  SEV_STYLE[f.severity],
                )}
              >
                {f.severity}
              </span>
              <span
                className="text-[10px] font-semibold"
                style={{ color: STATUS_META[f.status].color }}
              >
                {STATUS_META[f.status].label}
              </span>
            </span>
          </Link>
        </li>
      ))}
    </ol>
  );
}

export function CompactFindingList({ items, empty }: { items: PriorityItem[]; empty: string }) {
  if (!items.length) return <p className="text-xs text-muted-foreground">{empty}</p>;
  return (
    <ul className="space-y-2">
      {items.slice(0, 4).map((f) => (
        <li key={`${f.documentId}-${f.id}`}>
          <Link
            to="/analyze/$documentId"
            params={{ documentId: f.documentId }}
            className="block rounded-md border border-border/60 px-3 py-2 text-xs hover:bg-accent/15"
          >
            <b className="block truncate text-primary">{f.title}</b>
            <span className="block truncate text-muted-foreground">{f.documentName}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export function AlertsFeed({ events }: { events: ChangeEvent[] }) {
  if (!events.length) return <Empty>No version events recorded in the corpus.</Empty>;
  return (
    <ul className="space-y-3">
      {events.map((e) => (
        <li
          key={e.id}
          className="relative border-l-2 pl-3"
          style={{
            borderColor: e.severity === "high" ? "var(--chart-conflict)" : "var(--chart-gap)",
          }}
        >
          <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            <CalendarClock className="size-3" />
            {e.date} · {e.change}
          </p>
          <Link
            to="/standard/$id"
            params={{ id: e.standardId }}
            className="text-sm font-bold text-primary hover:underline"
          >
            {e.standard}
          </Link>
          <p className="line-clamp-2 text-[11px] leading-snug text-muted-foreground">{e.summary}</p>
          <p
            className={cn(
              "mt-0.5 text-[11px] font-semibold",
              e.affected.length ? "text-destructive" : "text-muted-foreground",
            )}
          >
            {e.affected.length
              ? `Affects ${e.affected.length} of your document${e.affected.length === 1 ? "" : "s"}`
              : "No document in this workspace affected"}
          </p>
        </li>
      ))}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// Activity
// ---------------------------------------------------------------------------

export function ActivityChart({ insights }: { insights: Insights }) {
  const total = insights.activity.reduce((s, d) => s + d.analyses, 0);
  return (
    <div>
      <p className="text-xs text-muted-foreground">
        <b className="text-lg text-primary tabular-nums">{inr(total)}</b> analyses in the last 14
        days (IST)
      </p>
      <div className="mt-2 h-32">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={insights.activity} margin={{ top: 6, right: 4, left: 4, bottom: 0 }}>
            <defs>
              <linearGradient id="actFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="var(--chart-accent)" stopOpacity={0.45} />
                <stop offset="100%" stopColor="var(--chart-accent)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              interval={3}
              tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                const p = active ? payload?.[0]?.payload : undefined;
                return p ? <ChartTip title={p.label} lines={[`${p.analyses} analyses`]} /> : null;
              }}
            />
            <Area
              type="monotone"
              dataKey="analyses"
              stroke="var(--chart-accent)"
              strokeWidth={2}
              fill="url(#actFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function RankedList({
  items,
  unit,
}: {
  items: Array<{ name: string; count: number; note?: string }>;
  unit: string;
}) {
  if (!items.length) return <p className="text-xs text-muted-foreground">Nothing yet.</p>;
  const max = Math.max(...items.map((i) => i.count));
  return (
    <ul className="space-y-2">
      {items.map((i) => (
        <li key={i.name} className="text-xs">
          <div className="flex items-center justify-between gap-2">
            <span className="truncate font-semibold text-primary" title={i.name}>
              {i.name}
            </span>
            <span className="shrink-0 text-muted-foreground">
              <b className="font-mono text-foreground">{inr(i.count)}</b> {unit}
              {i.note ? ` · ${i.note}` : ""}
            </span>
          </div>
          <div className="mt-1 h-1 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-[var(--chart-saffron)]"
              style={{ width: `${(i.count / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
