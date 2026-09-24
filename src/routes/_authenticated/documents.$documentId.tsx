import { createFileRoute, Link, notFound, useNavigate, useRouter } from "@tanstack/react-router";
import { ArrowLeft, ArrowRight, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
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
import type { ProcurementDocument } from "@/lib/contracts";
import { deleteDocument, getAnalysis, updateDocument } from "@/services/analysis";

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
  const open = doc.findings.filter((f) => f.status !== "verified");
  return (
    <div className="reveal">
      <Link
        to="/documents"
        className="flex items-center gap-2 text-sm font-bold text-muted-foreground"
      >
        <ArrowLeft className="size-4" />
        Document library
      </Link>
      <header className="mt-7">
        <p className="eyebrow">
          {doc.documentTypeLabel} · {doc.type} · {doc.organization}
        </p>
        <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
          <h1 className="font-display text-4xl text-primary sm:text-5xl">{doc.name}</h1>
          {!doc.isSample && <DocumentActions doc={doc} />}
        </div>
        <div className="mt-7 grid grid-cols-3 border-y border-border py-5">
          <Stat value={`${doc.readiness}%`} label="Readiness" />
          <Stat value={String(doc.standards)} label="Standards" />
          <Stat value={String(doc.issues)} label="Issues" />
        </div>
      </header>
      <section className="mt-12">
        <p className="eyebrow">Extracted content</p>
        <h2 className="section-title mt-2">Key Requirements</h2>
        <div className="mt-6 border-t border-border">
          {doc.requirements.length === 0 && (
            <p className="py-8 text-sm text-muted-foreground">
              No requirements were identified in this document.
            </p>
          )}
          {doc.requirements.map((r) => (
            <article key={r.id} className="thin-row grid gap-4 py-5 md:grid-cols-[1.5fr_1fr]">
              <div>
                <p className="text-sm font-semibold leading-6 text-primary">{r.text}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {r.category}
                  {r.sectionLabel ? ` · ${r.sectionLabel}` : ""}
                </p>
              </div>
              <div className="text-sm">
                <p className="font-bold text-accent-foreground">{r.standard}</p>
                <p className="mt-1 text-muted-foreground">{r.clause}</p>
                {r.confidence !== undefined && (
                  <p className="mt-1 text-xs text-muted-foreground" title={r.explanation}>
                    {r.basis === "explicit_reference"
                      ? "Cited in the requirement"
                      : `Retrieved · ${Math.round(r.confidence * 100)}% confidence`}
                  </p>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
      <section className="mt-12">
        <p className="eyebrow">Compliance</p>
        <h2 className="section-title mt-2">Open Findings</h2>
        <div className="mt-6">
          <FindingsList findings={open} onReview={onReview} />
        </div>
      </section>
      <Button asChild className="mt-10">
        <Link to="/analyze/$documentId" params={{ documentId: doc.id }}>
          Open full analysis <ArrowRight />
        </Link>
      </Button>
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="font-display text-3xl text-primary">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
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
          <Button variant="outline" size="sm">
            <Pencil /> Edit
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Edit document</DialogTitle>
            <DialogDescription>
              Changing the type re-analyses the document when the type changes how it is read.
            </DialogDescription>
          </DialogHeader>
          <label
            htmlFor="doc-name"
            className="text-xs font-bold uppercase tracking-[.08em] text-muted-foreground"
          >
            Name
          </label>
          <Input
            id="doc-name"
            value={name}
            maxLength={200}
            onChange={(e) => setName(e.target.value)}
          />
          <DocumentTypePicker id="edit-document-type" value={type} onChange={setType} />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button onClick={save} disabled={busy || !name.trim()}>
              {busy ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="outline" size="sm">
            <Trash2 /> Delete
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this document?</AlertDialogTitle>
            <AlertDialogDescription>
              {doc.name}: its analyses, review decisions and audit trail are deleted permanently.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={remove}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
