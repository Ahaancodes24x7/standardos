import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowUpDown,
  FilePlus2,
  FileText,
  Filter,
  Layers,
  Search,
  SlidersHorizontal,
} from "lucide-react";
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
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";

export const Route = createFileRoute("/_authenticated/documents/")({
  loader: () => listDocuments(),
  head: () => ({
    meta: [
      { title: "Document Library — STANDARDOS" },
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
    <div className="reveal space-y-8">
      {/* Header */}
      <PageHeader
        eyebrow="Workspace / Documents"
        title="Document Library"
        description="Comprehensive repository of analyzed procurement specifications, tenders, BOQs, datasheets, and test reports with live compliance states."
      >
        <Button asChild size="sm" className="gap-2 shadow-xs">
          <Link to="/analyze">
            <FilePlus2 className="size-4" />
            <span>Analyze New Document</span>
          </Link>
        </Button>
      </PageHeader>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border/80 bg-card/60 p-4">
        <div className="relative min-w-[240px] flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search specification name, organization, or document type..."
            className="pl-9 text-xs bg-background"
          />
        </div>

        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-40 text-xs bg-background">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="Analyzed">Analyzed</SelectItem>
            <SelectItem value="Review required">Review Required</SelectItem>
            <SelectItem value="Processing">Processing</SelectItem>
            <SelectItem value="Failed">Failed</SelectItem>
          </SelectContent>
        </Select>

        <Select value={docType} onValueChange={setDocType}>
          <SelectTrigger className="w-48 text-xs bg-background" aria-label="Document type">
            <SelectValue placeholder="Document Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Document Types</SelectItem>
            {DOCUMENT_TYPES.map((t) => (
              <SelectItem key={t.key} value={t.key}>
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setAsc(!asc)}
          className="gap-1.5 text-xs bg-background"
        >
          <ArrowUpDown className="size-3.5" />
          <span>Sort {asc ? "A-Z" : "Z-A"}</span>
        </Button>
      </div>

      {/* Documents Table */}
      <div className="intel-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] text-left text-sm">
            <thead>
              <tr className="border-b border-border/70 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                <th className="py-3.5 px-5">Specification</th>
                <th className="py-3.5 px-3">Type</th>
                <th className="py-3.5 px-3">Status</th>
                <th className="py-3.5 px-3">Standards</th>
                <th className="py-3.5 px-3">Issues</th>
                <th className="py-3.5 px-3">Readiness</th>
                <th className="py-3.5 pr-5 text-right">Analyzed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {rows.map((doc) => (
                <tr
                  key={doc.id}
                  className="group transition-colors hover:bg-accent/20 cursor-pointer"
                  onClick={() => {
                    window.location.href = `/documents/${doc.id}`;
                  }}
                >
                  <td className="py-4 px-5">
                    <Link
                      to="/documents/$documentId"
                      params={{ documentId: doc.id }}
                      className="font-bold text-primary hover:text-accent-foreground block truncate max-w-sm"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {doc.name}
                    </Link>
                    <span className="text-xs text-muted-foreground">{doc.organization}</span>
                  </td>

                  <td className="py-4 px-3">
                    <span className="text-xs font-semibold text-primary block">
                      {doc.documentTypeLabel}
                    </span>
                    <span className="font-mono text-[10px] uppercase text-muted-foreground">
                      {doc.type}
                    </span>
                  </td>

                  <td className="py-4 px-3">
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

                  <td className="py-4 px-3 font-mono text-xs font-semibold text-foreground">
                    {doc.standards}
                  </td>

                  <td className="py-4 px-3">
                    <span
                      className={`font-mono text-xs font-bold ${
                        doc.issues > 2 ? "text-destructive" : "text-muted-foreground"
                      }`}
                    >
                      {doc.issues}
                    </span>
                  </td>

                  <td className="py-4 px-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-secondary">
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

                  <td className="py-4 pr-5 text-right text-xs text-muted-foreground">
                    {formatAnalyzedAt(doc.analyzedAt)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {!rows.length && (
          <div className="py-16 text-center space-y-3">
            <FileText className="mx-auto size-8 text-muted-foreground/60" />
            <p className="text-sm font-bold text-primary">
              {documents.length
                ? "No documents match these filters."
                : "No documents analysed yet."}
            </p>
            {documents.length ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setQuery("");
                  setStatus("all");
                  setDocType("all");
                }}
              >
                Clear all filters
              </Button>
            ) : (
              <Button asChild size="sm">
                <Link to="/analyze">Analyze your first specification</Link>
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
