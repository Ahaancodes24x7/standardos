import { createFileRoute } from "@tanstack/react-router";
import {
  AlertCircle,
  Clock,
  Command,
  FileText,
  Filter,
  Search as SearchIcon,
  SlidersHorizontal,
  Sparkles,
  Upload,
} from "lucide-react";
import { useEffect, useState } from "react";
import { EmptySearch } from "@/components/app-shell";
import { StandardResultCard } from "@/components/standard-result";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { SearchResult } from "@/lib/contracts";
import { searchStandards } from "@/services/analysis";
import { PageHeader } from "@/components/shared/page-header";

export const Route = createFileRoute("/search")({
  head: () => ({
    meta: [
      { title: "Search Indian Standards — STANDARDOS" },
      {
        name: "description",
        content: "Search BIS standards using product descriptions, tender clauses or documents.",
      },
      { property: "og:title", content: "Standards Search — STANDARDOS" },
      {
        property: "og:description",
        content: "Clause-level Indian Standards search with explainable matches.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SearchPage,
});

type YearRange = "2020-" | "2010-2019" | "-2009";
const DOMAINS = ["Electrical", "Civil", "Mechanical", "Water & Environment"];
const YEARS: Array<[string, YearRange]> = [
  ["2020–present", "2020-"],
  ["2010–2019", "2010-2019"],
  ["Before 2010", "-2009"],
];

function SearchPage() {
  const [query, setQuery] = useState(
    "1.1 kV PVC-insulated copper wiring with overload protection and continuous earthing",
  );
  const [excerpt, setExcerpt] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [language, setLanguage] = useState("English");
  const [domains, setDomains] = useState<string[]>([]);
  const [years, setYears] = useState<YearRange[]>([]);

  const runSearch = async (text: string) => {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    try {
      setResults(await searchStandards(text, { domains, yearRanges: years }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  };

  const readFile = async (file: File | undefined) => {
    if (!file) return;
    if (!/\.txt$/i.test(file.name)) {
      setError(
        "Upload a .txt excerpt here. To analyse a full PDF or DOCX specification, sign in and use Analyze.",
      );
      return;
    }
    const text = (await file.text()).slice(0, 5000);
    setExcerpt(text);
    void runSearch(text);
  };

  useEffect(() => {
    void runSearch(query);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (results) void runSearch(query || excerpt);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [domains, years]);

  const toggle = <T,>(list: T[], value: T) =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value];

  return (
    <div className="reveal site-container py-8 space-y-8">
      {/* Header */}
      <PageHeader
        eyebrow="Standards Intelligence"
        title="Search Requirements & Clauses"
        description="Describe product specifications or tender obligations in plain language. StandardOS returns ranked evidence and clause citations directly from the Indian Standards knowledge graph."
      />

      {/* Command Center Input Card */}
      <div className="intel-card p-6 space-y-6">
        <Tabs defaultValue="query" className="w-full">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border/70 pb-4">
            <TabsList className="grid w-full grid-cols-3 max-w-sm">
              <TabsTrigger value="query" className="gap-1.5 text-xs">
                <SearchIcon className="size-3.5" />
                <span>Query</span>
              </TabsTrigger>
              <TabsTrigger value="excerpt" className="gap-1.5 text-xs">
                <FileText className="size-3.5" />
                <span>Excerpt</span>
              </TabsTrigger>
              <TabsTrigger value="file" className="gap-1.5 text-xs">
                <Upload className="size-3.5" />
                <span>File</span>
              </TabsTrigger>
            </TabsList>

            <div className="flex items-center gap-2">
              <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Language
              </label>
              <select
                className="rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold text-primary"
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
              >
                <option>English</option>
                <option>Hindi</option>
              </select>
            </div>
          </div>

          <TabsContent value="query" className="mt-4">
            <form
              className="flex flex-col gap-3 sm:flex-row sm:items-center"
              onSubmit={(e) => {
                e.preventDefault();
                void runSearch(query);
              }}
            >
              <div className="relative flex-1">
                <SearchIcon className="absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="h-12 pl-10 text-sm bg-background font-medium"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Describe a material, specification parameter, or engineering requirement…"
                />
              </div>
              <Button size="lg" type="submit" className="h-12 gap-2 shadow-xs shrink-0">
                <SearchIcon className="size-4" />
                <span>Find Standards</span>
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="excerpt" className="mt-4 space-y-3">
            <Textarea
              className="min-h-32 text-xs font-mono"
              value={excerpt}
              onChange={(e) => setExcerpt(e.target.value)}
              maxLength={5000}
              placeholder="Paste one or more tender clauses or BOQ specifications here…"
            />
            <Button size="sm" onClick={() => void runSearch(excerpt)} className="gap-2">
              <SearchIcon className="size-3.5" />
              <span>Analyze Excerpt</span>
            </Button>
          </TabsContent>

          <TabsContent value="file" className="mt-4">
            <label className="grid min-h-36 cursor-pointer place-items-center rounded-xl border-2 border-dashed border-border/80 bg-background/50 p-6 text-center hover:bg-card transition">
              <div className="space-y-1.5">
                <Upload className="mx-auto size-6 text-accent-foreground" />
                <p className="text-xs font-bold text-primary">Choose a TXT specification excerpt</p>
                <p className="text-[11px] text-muted-foreground">
                  First 5,000 characters analyzed. Sign in for complete multi-page PDF/DOCX
                  processing.
                </p>
              </div>
              <input
                type="file"
                accept=".txt"
                className="sr-only"
                onChange={(e) => void readFile(e.target.files?.[0])}
              />
            </label>
          </TabsContent>
        </Tabs>
      </div>

      {/* Search Grid */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Facets Sidebar */}
        <aside className="intel-card p-5 space-y-5 lg:col-span-3 self-start lg:sticky lg:top-20">
          <div className="flex items-center gap-2 border-b border-border/70 pb-3">
            <SlidersHorizontal className="size-4 text-accent-foreground" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-primary">
              Refine Facets
            </h2>
          </div>

          <fieldset className="space-y-2.5">
            <legend className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              Product Domain
            </legend>
            <div className="grid gap-2">
              {DOMAINS.map((value) => (
                <label key={value} className="flex items-center gap-2 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    className="accent-accent-foreground"
                    checked={domains.includes(value)}
                    onChange={() => setDomains(toggle(domains, value))}
                  />
                  <span className="text-primary font-medium">{value}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="space-y-2.5 border-t border-border/60 pt-4">
            <legend className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              Publication Edition
            </legend>
            <div className="grid gap-2">
              {YEARS.map(([label, value]) => (
                <label key={value} className="flex items-center gap-2 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    className="accent-accent-foreground"
                    checked={years.includes(value)}
                    onChange={() => setYears(toggle(years, value))}
                  />
                  <span className="text-primary font-medium">{label}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </aside>

        {/* Results Area */}
        <section className="space-y-4 lg:col-span-9">
          <div className="flex items-center justify-between border-b border-border/70 pb-2">
            <div>
              <p className="font-bold text-primary text-sm">
                {results ? "Ranked Governing Standards" : "Awaiting Search"}
              </p>
              {results && (
                <p className="text-xs text-muted-foreground">
                  {results.length} ranked matches mapped to your query
                </p>
              )}
            </div>
          </div>

          {language === "Hindi" && (
            <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-xs text-warning-foreground">
              Hindi-language semantic retrieval is in development. Results currently indexed in
              English.
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive"
            >
              <AlertCircle className="size-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="grid gap-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="intel-card h-48 animate-pulse bg-card/60" />
              ))}
            </div>
          ) : !results || !results.length ? (
            <EmptySearch />
          ) : (
            <div className="grid gap-4">
              {results.map((result) => (
                <StandardResultCard key={result.standard.id} result={result} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
