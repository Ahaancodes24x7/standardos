import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowUpDown, FilePlus2, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { formatAnalyzedAt, listDocuments } from "@/services/analysis";
import { DOCUMENT_TYPES } from "@/lib/document-types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export const Route = createFileRoute("/_authenticated/documents/")({
  loader: () => listDocuments(),
  head: () => ({
    meta: [
      { title: "Documents — STANDARDOS" },
      { name: "description", content: "Search and review analyzed procurement specifications." },
      { property: "og:title", content: "Documents — STANDARDOS" },
      { property: "og:description", content: "Procurement document library." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Documents,
});

function Documents() {
  const documents = Route.useLoaderData();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [docType, setDocType] = useState("all");
  const [asc, setAsc] = useState(false);
  const rows = useMemo(
    () =>
      documents
        .filter(
          (d) =>
            (d.name + d.organization + d.documentTypeLabel)
              .toLowerCase()
              .includes(query.toLowerCase()) &&
            (status === "all" || d.status === status) &&
            (docType === "all" || d.documentType === docType),
        )
        .sort((a, b) => (asc ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name))),
    [documents, query, status, docType, asc],
  );
  return (
    <div className="reveal">
      <header className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="eyebrow">Workspace / Documents</p>
          <h1 className="page-title mt-3">Document Library</h1>
          <p className="mt-4 text-muted-foreground">
            Every document you have analysed (specifications, tenders, BOQs, datasheets, reports and
            your own document types) with its latest compliance state.
          </p>
        </div>
        <Button asChild>
          <Link to="/analyze">
            <FilePlus2 />
            Analyze new
          </Link>
        </Button>
      </header>
      <div className="mt-10 flex flex-wrap gap-3 border-y border-border py-4">
        <div className="relative min-w-64 flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search name or organization…"
            className="pl-9"
          />
        </div>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="Analyzed">Analyzed</SelectItem>
            <SelectItem value="Review required">Review required</SelectItem>
            <SelectItem value="Processing">Processing</SelectItem>
            <SelectItem value="Failed">Failed</SelectItem>
          </SelectContent>
        </Select>
        <Select value={docType} onValueChange={setDocType}>
          <SelectTrigger className="w-52" aria-label="Document type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All document types</SelectItem>
            {DOCUMENT_TYPES.map((t) => (
              <SelectItem key={t.key} value={t.key}>
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={() => setAsc(!asc)}>
          <ArrowUpDown />
          Name
        </Button>
      </div>
      <div className="mt-6 overflow-x-auto">
        <div className="min-w-[820px]">
          <div className="grid grid-cols-[2.2fr_1fr_.6fr_.5fr_.6fr_.8fr] gap-5 border-b border-border pb-3 text-[10px] font-bold uppercase tracking-[.1em] text-muted-foreground">
            <span>Name</span>
            <span>Type</span>
            <span>Standards</span>
            <span>Issues</span>
            <span>Readiness</span>
            <span>Last analyzed</span>
          </div>
          {rows.map((doc) => (
            <Link
              key={doc.id}
              to="/documents/$documentId"
              params={{ documentId: doc.id }}
              className="thin-row grid grid-cols-[2.2fr_1fr_.6fr_.5fr_.6fr_.8fr] items-center gap-5 py-5 text-sm"
            >
              <span>
                <b className="block text-primary">{doc.name}</b>
                <small className="text-muted-foreground">
                  {doc.organization}
                  {doc.status === "Failed" || doc.status === "Processing" ? ` · ${doc.status}` : ""}
                </small>
              </span>
              <span>
                <span className="block text-primary">{doc.documentTypeLabel}</span>
                <small className="text-muted-foreground">{doc.type}</small>
              </span>
              <span>{doc.standards}</span>
              <span className={doc.issues > 2 ? "font-bold text-warning-foreground" : ""}>
                {doc.issues}
              </span>
              <span className="font-bold text-primary">
                {doc.runStatus === "succeeded" ? `${doc.readiness}%` : "—"}
              </span>
              <span className="text-muted-foreground">{formatAnalyzedAt(doc.analyzedAt)}</span>
            </Link>
          ))}
        </div>
      </div>
      {!rows.length && (
        <div className="py-20 text-center">
          {documents.length ? (
            <>
              <p className="font-bold text-primary">No documents match these filters.</p>
              <Button
                variant="link"
                onClick={() => {
                  setQuery("");
                  setStatus("all");
                  setDocType("all");
                }}
              >
                Clear filters
              </Button>
            </>
          ) : (
            <>
              <p className="font-bold text-primary">No documents analysed yet.</p>
              <Button asChild variant="link">
                <Link to="/analyze">Analyze your first document</Link>
              </Button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
