import { createFileRoute } from "@tanstack/react-router";
import { FileText, Search as SearchIcon, SlidersHorizontal, Upload } from "lucide-react";
import { useState } from "react";
import { PageIntro, EmptySearch } from "@/components/app-shell";
import { StandardResultCard } from "@/components/standard-result";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { searchResults } from "@/lib/standards";

export const Route = createFileRoute("/search")({ head: () => ({ meta: [{ title: "Search Indian Standards — StandardOS" }, { name: "description", content: "Search BIS standards using product descriptions, tender clauses or documents." }, { property: "og:title", content: "Standards Search — StandardOS" }, { property: "og:description", content: "Clause-level Indian Standards search with explainable matches." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" }] }), component: SearchPage });

function SearchPage() {
  const [query, setQuery] = useState("1.1 kV PVC-insulated copper wiring with overload protection and continuous earthing");
  const [searched, setSearched] = useState(true);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState("English");
  const runSearch = () => { setLoading(true); setSearched(true); window.setTimeout(() => setLoading(false), 850); };
  return <div className="page-wrap pb-20 pt-8"><PageIntro eyebrow="Standards intelligence" title="Search requirements, not catalog titles." description="Describe the product or obligation in plain language. StandardOS will return ranked evidence, not just keywords." />
    <div className="glass-panel mt-8 p-4 sm:p-6"><div className="flex flex-wrap items-center justify-between gap-3"><Tabs defaultValue="query" className="w-full"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><TabsList><TabsTrigger value="query"><SearchIcon/> Query</TabsTrigger><TabsTrigger value="excerpt"><FileText/> Tender excerpt</TabsTrigger><TabsTrigger value="file"><Upload/> Upload file</TabsTrigger></TabsList><label className="flex items-center gap-2 text-sm font-semibold text-primary">Language<select className="rounded-sm border border-input bg-background/70 px-3 py-2" value={language} onChange={(event)=>setLanguage(event.target.value)}><option>English</option><option>Hindi</option></select></label></div>
      <TabsContent value="query"><div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]"><Input className="h-14 bg-background/55 px-5 text-base" value={query} onChange={(event)=>setQuery(event.target.value)} placeholder="Describe a product, material or requirement…"/><Button size="lg" onClick={runSearch}><SearchIcon/> Find standards</Button></div></TabsContent>
      <TabsContent value="excerpt"><Textarea className="mt-4 min-h-36 bg-background/55 p-4" placeholder="Paste one or more tender clauses here…"/><Button className="mt-3" onClick={runSearch}><SearchIcon/> Analyse excerpt</Button></TabsContent>
      <TabsContent value="file"><label className="mt-4 grid min-h-40 cursor-pointer place-items-center border border-dashed border-input bg-background/35 text-center"><span><Upload className="mx-auto mb-3 text-accent-foreground"/><b className="text-primary">Choose a PDF or DOC file</b><small className="mt-1 block text-muted-foreground">Up to 20 MB · mock upload</small></span><input type="file" accept=".pdf,.doc,.docx" className="sr-only" onChange={runSearch}/></label></TabsContent></Tabs></div></div>
    <div className="mt-8 grid gap-6 lg:grid-cols-[15rem_minmax(0,1fr)]"><aside className="glass-panel h-fit p-5 lg:sticky lg:top-28"><h2 className="flex items-center gap-2 font-serif text-xl text-primary"><SlidersHorizontal className="size-4"/> Refine</h2>{[["Domain",["Electrical","Civil Engineering","Materials","Water & Environment"]],["Publication year",["2020–present","2010–2019","Before 2010"]],["Document language",["English","Hindi","Bilingual"]]].map(([title,values])=><fieldset key={title as string} className="mt-6 border-t border-border pt-5"><legend className="text-xs font-bold uppercase tracking-[.1em] text-muted-foreground">{title as string}</legend><div className="mt-3 grid gap-2">{(values as string[]).map((value)=><label key={value} className="flex items-center gap-2 text-sm"><input type="checkbox" className="accent-accent-foreground"/> {value}</label>)}</div></fieldset>)}</aside>
      <section><div className="mb-4 flex items-baseline justify-between"><div><p className="font-serif text-2xl text-primary">{searched ? "Recommended standards" : "No search yet"}</p><p className="text-sm text-muted-foreground">{searched ? `${searchResults.length} ranked matches · ${language}` : ""}</p></div></div>{loading ? <div className="grid gap-4">{[1,2,3].map((item)=><div key={item} className="glass-panel h-64 animate-pulse bg-card/50"/>)}</div> : !searched || !query.trim() ? <EmptySearch/> : <div className="grid gap-4">{searchResults.map((result)=><StandardResultCard key={result.standard.id} result={result}/>)}</div>}</section>
    </div>
  </div>;
}