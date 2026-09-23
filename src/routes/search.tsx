import { createFileRoute } from "@tanstack/react-router";
import {
  AlertCircle,
  FileText,
  Search as SearchIcon,
  SlidersHorizontal,
  Upload,
} from "lucide-react";
import { useEffect, useState } from "react";
import { PageIntro, EmptySearch } from "@/components/app-shell";
import { StandardResultCard } from "@/components/standard-result";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { SearchResult } from "@/lib/contracts";
import { searchStandards } from "@/services/analysis";

export const Route = createFileRoute("/search")({
  head: () => ({
    meta: [
      { title: "Search Indian Standards — StandardOS" },
      {
        name: "description",
        content: "Search BIS standards using product descriptions, tender clauses or documents.",
      },
      { property: "og:title", content: "Standards Search — StandardOS" },
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
    // Run once for the example query; later searches are user-triggered.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (results) void runSearch(query || excerpt);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [domains, years]);

  const toggle = <T,>(list: T[], value: T) =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value];

  return (
    <div className="page-wrap pb-20 pt-8">
      <PageIntro
        eyebrow="Standards intelligence"
        title="Search requirements, not catalog titles."
        description="Describe the product or obligation in plain language. StandardOS will return ranked evidence, not just keywords."
      />
      <div className="glass-panel mt-8 p-4 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Tabs defaultValue="query" className="w-full">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <TabsList>
                <TabsTrigger value="query">
                  <SearchIcon /> Query
                </TabsTrigger>
                <TabsTrigger value="excerpt">
                  <FileText /> Tender excerpt
                </TabsTrigger>
                <TabsTrigger value="file">
                  <Upload /> Upload file
                </TabsTrigger>
              </TabsList>
              <label className="flex items-center gap-2 text-sm font-semibold text-primary">
                Language
                <select
                  className="rounded-sm border border-input bg-background/70 px-3 py-2"
                  value={language}
                  onChange={(event) => setLanguage(event.target.value)}
                >
                  <option>English</option>
                  <option>Hindi</option>
                </select>
              </label>
            </div>
            <TabsContent value="query">
              <form
                className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]"
                onSubmit={(e) => {
                  e.preventDefault();
                  void runSearch(query);
                }}
              >
                <Input
                  className="h-14 bg-background/55 px-5 text-base"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Describe a product, material or requirement…"
                />
                <Button size="lg" type="submit">
                  <SearchIcon /> Find standards
                </Button>
              </form>
            </TabsContent>
            <TabsContent value="excerpt">
              <Textarea
                className="mt-4 min-h-36 bg-background/55 p-4"
                value={excerpt}
                onChange={(e) => setExcerpt(e.target.value)}
                maxLength={5000}
                placeholder="Paste one or more tender clauses here…"
              />
              <Button className="mt-3" onClick={() => void runSearch(excerpt)}>
                <SearchIcon /> Analyse excerpt
              </Button>
            </TabsContent>
            <TabsContent value="file">
              <label className="mt-4 grid min-h-40 cursor-pointer place-items-center border border-dashed border-input bg-background/35 text-center">
                <span>
                  <Upload className="mx-auto mb-3 text-accent-foreground" />
                  <b className="text-primary">Choose a TXT excerpt</b>
                  <small className="mt-1 block text-muted-foreground">
                    First 5,000 characters are searched · full PDF/DOCX analysis is available after
                    sign-in
                  </small>
                </span>
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
      </div>
      <div className="mt-8 grid gap-6 lg:grid-cols-[15rem_minmax(0,1fr)]">
        <aside className="glass-panel h-fit p-5 lg:sticky lg:top-28">
          <h2 className="flex items-center gap-2 font-serif text-xl text-primary">
            <SlidersHorizontal className="size-4" /> Refine
          </h2>
          <fieldset className="mt-6 border-t border-border pt-5">
            <legend className="text-xs font-bold uppercase tracking-[.1em] text-muted-foreground">
              Domain
            </legend>
            <div className="mt-3 grid gap-2">
              {DOMAINS.map((value) => (
                <label key={value} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    className="accent-accent-foreground"
                    checked={domains.includes(value)}
                    onChange={() => setDomains(toggle(domains, value))}
                  />{" "}
                  {value}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset className="mt-6 border-t border-border pt-5">
            <legend className="text-xs font-bold uppercase tracking-[.1em] text-muted-foreground">
              Publication year
            </legend>
            <div className="mt-3 grid gap-2">
              {YEARS.map(([label, value]) => (
                <label key={value} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    className="accent-accent-foreground"
                    checked={years.includes(value)}
                    onChange={() => setYears(toggle(years, value))}
                  />{" "}
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
        </aside>
        <section>
          <div className="mb-4 flex items-baseline justify-between">
            <div>
              <p className="font-serif text-2xl text-primary">
                {results ? "Recommended standards" : "No search yet"}
              </p>
              <p className="text-sm text-muted-foreground">
                {results ? `${results.length} ranked matches · ${language}` : ""}
              </p>
            </div>
          </div>
          {language === "Hindi" && (
            <p className="mb-4 text-sm text-muted-foreground">
              Hindi-language retrieval is not supported yet; the corpus and query processing are
              English only.
            </p>
          )}
          {error && (
            <p role="alert" className="mb-4 flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="size-4" />
              {error}
            </p>
          )}
          {loading ? (
            <div className="grid gap-4">
              {[1, 2, 3].map((item) => (
                <div key={item} className="glass-panel h-64 animate-pulse bg-card/50" />
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
