import { Link } from "@tanstack/react-router";
import { Bookmark, ChevronDown, ExternalLink } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { SearchResult } from "@/lib/standards";

export function Confidence({ score }: { score: number }) {
  return <div className="flex items-center gap-2" aria-label={`${score}% confidence`}><div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-accent-foreground" style={{ width: `${score}%` }} /></div><span className="text-xs font-semibold text-primary">{score}% match</span></div>;
}

export function StandardResultCard({ result, compact = false }: { result: SearchResult; compact?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const [saved, setSaved] = useState(false);
  return <article className="glass-panel card-lift overflow-hidden p-5 sm:p-6">
    <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-4">
      <div className="min-w-0"><p className="eyebrow">{result.standard.number}</p><h3 className="mt-2 font-serif text-xl leading-snug text-primary sm:text-2xl">{result.standard.title}</h3></div>
      {!compact && <Button variant="ghost" size="icon" onClick={() => setSaved((value) => !value)} aria-label={saved ? "Remove bookmark" : "Bookmark standard"}><Bookmark className={saved ? "fill-current text-accent-foreground" : ""}/></Button>}
    </div>
    <div className="mt-4"><Confidence score={result.confidenceScore} /></div>
    <blockquote className="citation mt-5"><p className="text-xs font-semibold text-accent-foreground">{result.matchedClause.section}</p><p className="mt-2 text-sm leading-6 text-foreground">“{result.matchedClause.text}”</p></blockquote>
    {!compact && <>
      <Button variant="ghost" className="mt-3 w-full justify-between px-0 hover:bg-transparent" onClick={() => setExpanded((value) => !value)}>Why this was recommended <ChevronDown className={`transition-transform ${expanded ? "rotate-180" : ""}`} /></Button>
      {expanded && <div className="explanation mt-2 text-sm leading-6 text-muted-foreground">{result.explanation}</div>}
      <div className="mt-5 flex justify-end"><Button asChild variant="outline" size="sm"><Link to="/standard/$id" params={{ id: result.standard.id }}>Open standard <ExternalLink /></Link></Button></div>
    </>}
  </article>;
}