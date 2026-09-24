import { createFileRoute, Link } from "@tanstack/react-router";
import { ExternalLink, GitBranch, Layers, Search, ShieldCheck, Waypoints } from "lucide-react";
import { useMemo, useState } from "react";
import { getDependencyDag, listStandards } from "@/services/analysis";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/shared/page-header";
import { DagVisualizer } from "@/components/dag/dag-visualizer";

export const Route = createFileRoute("/_authenticated/standards")({
  loader: async () => {
    const [standards, dag] = await Promise.all([listStandards(), getDependencyDag()]);
    return { standards, dag };
  },
  head: () => ({
    meta: [
      { title: "Standards Explorer & DAG — STANDARDOS" },
      { name: "description", content: "Search Indian Standards and explore related requirements." },
      { property: "og:title", content: "Standards Explorer — STANDARDOS" },
      { property: "og:description", content: "Indian Standards relationship explorer." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Standards,
});

function Standards() {
  const { standards, dag } = Route.useLoaderData();
  const [viewMode, setViewMode] = useState<"catalog" | "dag">("catalog");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(standards[0]?.id);
  const [categoryFilter, setCategoryFilter] = useState("all");

  const categories = useMemo(() => {
    return Array.from(new Set(standards.map((s) => s.category))).filter(Boolean);
  }, [standards]);

  const results = useMemo(
    () =>
      standards.filter((s) => {
        const matchQuery = (s.number + s.title + s.category)
          .toLowerCase()
          .includes(query.toLowerCase());
        const matchCat = categoryFilter === "all" || s.category === categoryFilter;
        return matchQuery && matchCat;
      }),
    [standards, query, categoryFilter],
  );

  const selected = standards.find((s) => s.id === selectedId) ?? standards[0];

  return (
    <div className="reveal space-y-8">
      {/* Header */}
      <PageHeader
        eyebrow="Knowledge Graph Layer"
        title="Standards & Dependency DAG"
        description={`${standards.length} Indian Standards indexed across ${categories.length} product domains with full normative reference closure.`}
      >
        <div className="flex items-center rounded-lg border border-border bg-card p-1">
          <Button
            size="sm"
            variant={viewMode === "catalog" ? "default" : "ghost"}
            onClick={() => setViewMode("catalog")}
            className="h-8 gap-1.5 text-xs font-semibold"
          >
            <Waypoints className="size-3.5" />
            <span>Standards Catalog</span>
          </Button>
          <Button
            size="sm"
            variant={viewMode === "dag" ? "default" : "ghost"}
            onClick={() => setViewMode("dag")}
            className="h-8 gap-1.5 text-xs font-semibold"
          >
            <GitBranch className="size-3.5" />
            <span>Interactive DAG</span>
          </Button>
        </div>
      </PageHeader>

      {/* Mode 1: Interactive DAG */}
      {viewMode === "dag" && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              Pan, zoom, search, and click nodes to highlight upstream obligations and downstream
              dependents.
            </span>
          </div>
          <DagVisualizer
            dag={dag}
            initialSelectedId={selectedId}
            onSelectNode={(id) => setSelectedId(id)}
            height={620}
          />
        </section>
      )}

      {/* Mode 2: Catalog Explorer */}
      {viewMode === "catalog" && (
        <div className="space-y-6">
          {/* Search and Filters */}
          <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border/80 bg-card/60 p-4">
            <div className="relative min-w-[240px] flex-1">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="h-10 pl-9 text-xs bg-background"
                placeholder="Search Indian Standards by IS designation or title..."
              />
            </div>

            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              <button
                type="button"
                onClick={() => setCategoryFilter("all")}
                className={`rounded-lg px-2.5 py-1.5 font-semibold transition ${
                  categoryFilter === "all"
                    ? "bg-primary text-primary-foreground font-bold shadow-xs"
                    : "text-muted-foreground hover:bg-muted hover:text-primary"
                }`}
              >
                All ({standards.length})
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setCategoryFilter(cat)}
                  className={`rounded-lg px-2.5 py-1.5 font-semibold transition ${
                    categoryFilter === cat
                      ? "bg-primary text-primary-foreground font-bold shadow-xs"
                      : "text-muted-foreground hover:bg-muted hover:text-primary"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Two-Pane Knowledge Explorer */}
          <div className="grid gap-6 lg:grid-cols-12">
            {/* Left Column: Standards List */}
            <div className="intel-card divide-y divide-border/60 overflow-hidden lg:col-span-7 max-h-[700px] overflow-y-auto custom-scrollbar">
              {results.map((s) => {
                const isSelected = selected?.id === s.id;
                const isSuperseded = s.status === "Superseded" || s.status === "Withdrawn";

                return (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setSelectedId(s.id)}
                    className={`w-full p-4 text-left transition-all hover:bg-accent/20 flex flex-col gap-1.5 ${
                      isSelected
                        ? "border-l-4 border-l-accent-foreground bg-accent/20"
                        : "border-l-4 border-l-transparent"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <b className="font-mono text-sm text-primary">{s.number}</b>
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                          isSuperseded
                            ? "bg-warning/20 text-warning-foreground"
                            : "bg-success/20 text-success-foreground"
                        }`}
                      >
                        {s.status}
                      </span>
                    </div>
                    <p className="text-xs leading-relaxed text-muted-foreground line-clamp-2">
                      {s.title}
                    </p>
                    <div className="flex items-center gap-3 text-[11px] text-muted-foreground pt-1">
                      <span>{s.category}</span>
                      <span>·</span>
                      <span>{s.related.length} Normative Links</span>
                    </div>
                  </button>
                );
              })}

              {!results.length && (
                <div className="py-16 text-center text-xs text-muted-foreground">
                  No standards match your search query.
                </div>
              )}
            </div>

            {/* Right Column: Selected Standard Preview */}
            {selected && (
              <aside className="intel-card p-6 lg:col-span-5 space-y-6 self-start lg:sticky lg:top-20">
                <div className="border-b border-border/70 pb-4">
                  <div className="flex items-center justify-between">
                    <span className="eyebrow">{selected.category}</span>
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                        selected.status === "Superseded" || selected.status === "Withdrawn"
                          ? "bg-warning/20 text-warning-foreground"
                          : "bg-success/20 text-success-foreground"
                      }`}
                    >
                      {selected.status}
                    </span>
                  </div>
                  <h2 className="mt-2 font-mono text-2xl font-extrabold text-primary">
                    {selected.number}
                  </h2>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                    {selected.title}
                  </p>
                </div>

                {/* Conformity Strip */}
                <div className="flex items-center justify-between rounded-xl border border-border/80 bg-background/60 p-3.5 text-xs">
                  <span className="flex items-center gap-2 font-semibold text-primary">
                    <ShieldCheck className="size-4 text-accent-foreground" />
                    <span>Conformity Relevance:</span>
                  </span>
                  <span className="font-mono font-bold text-accent-foreground">
                    {selected.certification}
                  </span>
                </div>

                {/* Structured Knowledge Graph Connections */}
                <div className="space-y-3">
                  <p className="eyebrow">Normative Connections</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selected.related.map((rel) => (
                      <span
                        key={rel}
                        className="rounded-lg border border-border/80 bg-background/80 px-2.5 py-1 font-mono text-xs font-semibold text-primary"
                      >
                        {rel}
                      </span>
                    ))}
                    {!selected.related.length && (
                      <span className="text-xs text-muted-foreground">No references recorded.</span>
                    )}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="pt-2 border-t border-border/70 space-y-2">
                  <Button asChild size="sm" className="w-full gap-2">
                    <Link to="/standard/$id" params={{ id: selected.id }}>
                      <span>Open Full Record & Clauses</span>
                      <ExternalLink className="size-3.5" />
                    </Link>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full gap-2 text-xs"
                    onClick={() => {
                      setViewMode("dag");
                    }}
                  >
                    <GitBranch className="size-3.5 text-accent-foreground" />
                    <span>Focus in Dependency DAG</span>
                  </Button>
                </div>
              </aside>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
