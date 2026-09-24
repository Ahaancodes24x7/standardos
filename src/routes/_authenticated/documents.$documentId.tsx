import { createFileRoute, Link, notFound, useNavigate, useRouter } from "@tanstack/react-router";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  ExternalLink,
  Layers,
  Pencil,
  Search,
  ShieldAlert,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  DocumentTypePicker,
  type DocumentTypeValue,
} from "@/components/analysis/document-type-picker";
import { FindingsList } from "@/components/analysis/findings";
import { useReviewActions } from "@/components/analysis/use-review";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { ProcurementDocument, Requirement } from "@/lib/contracts";
import { deleteDocument, getAnalysis, updateDocument } from "@/services/analysis";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { EvidenceDrawer } from "@/components/shared/evidence-drawer";

export const Route = createFileRoute("/_authenticated/documents/$documentId")({
  loader: async ({ params }) => {
    const document = await getAnalysis(params.documentId);
    if (!document) throw notFound();
    return document;
  },
  component: Detail,
});

function Detail() {
  const doc = Route.useLoaderData();
  const { onReview } = useReviewActions([doc]);
  const [selectedReq, setSelectedReq] = useState<Requirement | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [reqSearch, setReqSearch] = useState("");
  const [reqCategory, setReqCategory] = useState("all");

  const openFindings = doc.findings.filter((f) => f.status !== "verified");

  const categories = useMemo(() => {
    return Array.from(new Set(doc.requirements.map((r) => r.category))).filter(Boolean);
  }, [doc.requirements]);

  const filteredRequirements = useMemo(() => {
    return doc.requirements.filter((r) => {
      const matchCat = reqCategory === "all" || r.category === reqCategory;
      const matchQuery =
        !reqSearch.trim() ||
        (r.text + r.standard + r.clause).toLowerCase().includes(reqSearch.toLowerCase());
      return matchCat && matchQuery;
    });
  }, [doc.requirements, reqCategory, reqSearch]);

  return (
    <div className="reveal space-y-8">
      {/* Back button */}
      <div>
        <Link
          to="/documents"
          className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-primary transition"
        >
          <ArrowLeft className="size-3.5" />
          <span>Back to Document Library</span>
        </Link>
      </div>

      {/* Header */}
      <PageHeader
        eyebrow={`${doc.documentTypeLabel} · ${doc.type} · ${doc.organization}`}
        title={doc.name}
        description="Detailed specification extraction and compliance audit trail."
      >
        <div className="flex items-center gap-2">
          {!doc.isSample && <DocumentActions doc={doc} />}
          <Button asChild size="sm" className="gap-2 shadow-xs">
            <Link to="/analyze/$documentId" params={{ documentId: doc.id }}>
              <span>Open Full Analysis</span>
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </PageHeader>

      {/* Metric Cards */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <MetricCard
          label="Specification Readiness"
          value={`${doc.readiness}%`}
          icon={ShieldCheck}
          subtitle="Overall compliance score"
          trend={{
            value: doc.readiness >= 80 ? "Pass readiness" : "Review required",
            positive: doc.readiness >= 80,
          }}
        />
        <MetricCard
          label="Mapped Standards"
          value={doc.standards}
          icon={BookOpen}
          subtitle="Indian Standards referenced"
          trend={{ value: `${doc.requirements.length} obligations`, neutral: true }}
        />
        <MetricCard
          label="Flagged Issues"
          value={doc.issues}
          icon={ShieldAlert}
          subtitle={`${openFindings.length} open for review`}
          trend={{
            value: openFindings.length === 0 ? "Resolved" : "Attention needed",
            positive: openFindings.length === 0,
          }}
        />
      </section>

      {/* Key Requirements Data Interface */}
      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-3">
          <div>
            <p className="eyebrow">Extracted Obligations</p>
            <h2 className="text-xl font-bold text-primary">Key Requirements</h2>
          </div>
          <span className="text-xs text-muted-foreground">
            Click any row to open the detailed requirement drawer
          </span>
        </div>

        {/* Filter bar for requirements */}
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border/80 bg-card/60 p-3">
          <div className="relative min-w-[200px] flex-1">
            <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={reqSearch}
              onChange={(e) => setReqSearch(e.target.value)}
              placeholder="Search requirement wording, standard, or clause..."
              className="h-8 pl-8 text-xs bg-background"
            />
          </div>

          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <button
              type="button"
              onClick={() => setReqCategory("all")}
              className={`rounded-lg px-2.5 py-1 font-semibold transition ${
                reqCategory === "all"
                  ? "bg-primary text-primary-foreground font-bold"
                  : "text-muted-foreground hover:bg-muted hover:text-primary"
              }`}
            >
              All Categories ({doc.requirements.length})
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setReqCategory(cat)}
                className={`rounded-lg px-2.5 py-1 font-semibold transition ${
                  reqCategory === cat
                    ? "bg-primary text-primary-foreground font-bold"
                    : "text-muted-foreground hover:bg-muted hover:text-primary"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Requirements Table */}
        <div className="intel-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="border-b border-border/70 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  <th className="py-3 px-4">Requirement</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Governing Standard</th>
                  <th className="py-3 px-3">Clause</th>
                  <th className="py-3 px-3 text-right">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {filteredRequirements.map((r) => (
                  <tr
                    key={r.id}
                    className="group transition-colors hover:bg-accent/20 cursor-pointer"
                    onClick={() => {
                      setSelectedReq(r);
                      setDrawerOpen(true);
                    }}
                  >
                    <td className="py-3.5 px-4 max-w-md">
                      <p className="font-semibold text-primary group-hover:text-accent-foreground transition truncate">
                        {r.text}
                      </p>
                      {r.sectionLabel && (
                        <span className="text-[10px] text-muted-foreground">{r.sectionLabel}</span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 text-xs text-muted-foreground font-medium">
                      {r.category}
                    </td>
                    <td className="py-3.5 px-3 font-mono text-xs font-bold text-accent-foreground">
                      {r.standard}
                    </td>
                    <td className="py-3.5 px-3 text-xs text-muted-foreground">
                      {r.clause || "General Provision"}
                    </td>
                    <td className="py-3.5 px-3 text-right font-mono text-xs font-bold text-primary">
                      {r.confidence !== undefined ? `${Math.round(r.confidence * 100)}%` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {!filteredRequirements.length && (
            <div className="py-12 text-center text-xs text-muted-foreground">
              No requirements match your current search or category filter.
            </div>
          )}
        </div>
      </section>

      {/* Open Findings Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b border-border/70 pb-3">
          <div>
            <p className="eyebrow">Action Required</p>
            <h2 className="text-xl font-bold text-primary">
              Open Findings ({openFindings.length})
            </h2>
          </div>
          <span className="text-xs text-muted-foreground">
            Review and record reviewer sign-offs
          </span>
        </div>
        <FindingsList findings={openFindings} onReview={onReview} />
      </section>

      {/* Requirement Inspector Drawer */}
      <EvidenceDrawer requirement={selectedReq} open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}

function DocumentActions({ doc }: { doc: ProcurementDocument }) {
  const router = useRouter();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(doc.name);
  const [type, setType] = useState<DocumentTypeValue>({
    documentType: doc.documentType,
    documentTypeLabel: doc.documentType === "other" ? doc.documentTypeLabel : "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function save() {
    if (type.documentType === "other" && !type.documentTypeLabel.trim()) {
      setError("Name the document type when you choose Other.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await updateDocument(doc.id, {
        name,
        documentType: type.documentType,
        ...(type.documentType === "other" ? { documentTypeLabel: type.documentTypeLabel } : {}),
      });
      setOpen(false);
      await router.invalidate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "The document could not be updated.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    await deleteDocument(doc.id);
    await navigate({ to: "/documents" });
  }

  return (
    <div className="flex gap-2">
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs">
            <Pencil className="size-3.5" /> <span>Edit</span>
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Edit Document Metadata</DialogTitle>
            <DialogDescription>
              Changing the type re-analyses the document when the type changes how it is read.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="space-y-1">
              <label
                htmlFor="doc-name"
                className="text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground"
              >
                Specification Name
              </label>
              <Input
                id="doc-name"
                value={name}
                maxLength={200}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <DocumentTypePicker id="edit-document-type" value={type} onChange={setType} />
            {error && <p className="text-xs text-destructive font-semibold">{error}</p>}
          </div>
          <DialogFooter>
            <Button onClick={save} disabled={busy || !name.trim()} size="sm">
              {busy ? "Saving…" : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 text-xs text-destructive hover:bg-destructive/10"
          >
            <Trash2 className="size-3.5" /> <span>Delete</span>
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this specification?</AlertDialogTitle>
            <AlertDialogDescription>
              {doc.name}: its analyses, review decisions, and audit trail will be permanently
              removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={remove}
              className="bg-destructive text-destructive-foreground"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
