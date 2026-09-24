import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  AlertCircle,
  ArrowRight,
  Check,
  CheckCircle2,
  Cpu,
  FileSearch,
  FileText,
  Loader2,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";
import { useRef, useState } from "react";
import { analyzeDocument } from "@/services/analysis";
import {
  DocumentTypePicker,
  type DocumentTypeValue,
} from "@/components/analysis/document-type-picker";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { PageHeader } from "@/components/shared/page-header";

export const Route = createFileRoute("/_authenticated/analyze/")({
  head: () => ({
    meta: [
      { title: "Analyze a Specification — STANDARDOS" },
      {
        name: "description",
        content:
          "Upload or paste a procurement specification for standards and compliance analysis.",
      },
      { property: "og:title", content: "Analyze a Specification — STANDARDOS" },
      { property: "og:description", content: "Map standards and detect compliance issues." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AnalyzePage,
});

const PIPELINE_STAGES = [
  { id: 1, title: "Parsing Document", desc: "Zoning & section segmentation" },
  { id: 2, title: "Requirement Extraction", desc: "NLP attribute identification" },
  { id: 3, title: "Domain Classification", desc: "Hybrid embedding & lexicon" },
  { id: 4, title: "Standards Retrieval", desc: "Mapping applicable BIS standards" },
  { id: 5, title: "Graph Reasoning", desc: "Normative reference & DAG resolution" },
  { id: 6, title: "Conformity Audit", desc: "Mandatory certification & test checks" },
  { id: 7, title: "Conflict Detection", desc: "Contradiction & obsolescence discovery" },
  { id: 8, title: "Compliance Synthesis", desc: "Evidence trail & repair generation" },
];

function AnalyzePage() {
  const nav = useNavigate();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const [running, setRunning] = useState(false);
  const [docType, setDocType] = useState<DocumentTypeValue>({
    documentType: "specification",
    documentTypeLabel: "",
  });

  const validate = (candidate: File) => {
    const ext = candidate.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "txt"].includes(ext ?? "")) {
      setError("Unsupported file. Upload PDF, DOCX, or TXT.");
      return;
    }
    if (candidate.size > 20 * 1024 * 1024) {
      setError("Upload failed. The maximum file size is 20 MB.");
      return;
    }
    setError("");
    setFile(candidate);
  };

  const run = async () => {
    if (!file && !text.trim()) {
      setError("Add a file or paste specification text before analysis.");
      return;
    }
    if (docType.documentType === "other" && !docType.documentTypeLabel.trim()) {
      setError("Name the document type when you choose Other.");
      return;
    }
    setRunning(true);
    setError("");
    try {
      const result = await analyzeDocument(
        {
          file: file ?? undefined,
          text: text || undefined,
          documentType: docType.documentType,
          documentTypeLabel: docType.documentTypeLabel,
        },
        setProgress,
      );
      await nav({ to: "/analyze/$documentId", params: { documentId: result.id } });
    } catch (err) {
      setError(
        err instanceof Error && err.message
          ? err.message
          : "Analysis failed because the service could not respond. Your document is safe; please retry.",
      );
      setRunning(false);
      setProgress(0);
    }
  };

  return (
    <div className="reveal max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <PageHeader
        eyebrow="Intelligence Pipeline"
        title="Analyze a Specification"
        description="Extract requirements, map Indian Standards, verify normative dependencies, and generate clause-level evidence."
      />

      {running ? (
        <Processing progress={progress} />
      ) : (
        <div className="space-y-6">
          {/* Analysis Workflow Overview Strip */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-5 rounded-xl border border-border/70 bg-card/60 p-3 text-center text-xs">
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase text-muted-foreground">Input</span>
              <p className="font-semibold text-primary">1. Document</p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase text-muted-foreground">NLP</span>
              <p className="font-semibold text-primary">2. Requirements</p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase text-muted-foreground">Corpus</span>
              <p className="font-semibold text-primary">3. Standards</p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase text-muted-foreground">DAG</span>
              <p className="font-semibold text-primary">4. Reasoning</p>
            </div>
            <div className="col-span-2 sm:col-span-1 space-y-1">
              <span className="text-[10px] font-bold uppercase text-muted-foreground">Outcome</span>
              <p className="font-semibold text-accent-foreground">5. Findings</p>
            </div>
          </div>

          {/* Main Input Card */}
          <section className="intel-card p-6 sm:p-8 space-y-6">
            {/* Document Type Selector */}
            <div className="border-b border-border/70 pb-6">
              <DocumentTypePicker value={docType} onChange={setDocType} />
            </div>

            {/* Upload or Paste Tabs */}
            <Tabs defaultValue="upload" className="w-full">
              <TabsList className="grid w-full grid-cols-2 max-w-xs">
                <TabsTrigger value="upload" className="gap-2">
                  <UploadCloud className="size-4" />
                  <span>Upload File</span>
                </TabsTrigger>
                <TabsTrigger value="paste" className="gap-2">
                  <FileText className="size-4" />
                  <span>Paste Text</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="upload" className="mt-5 space-y-4">
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDrag(true);
                  }}
                  onDragLeave={() => setDrag(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDrag(false);
                    const dropped = e.dataTransfer.files[0];
                    if (dropped) validate(dropped);
                  }}
                  className={`grid min-h-60 place-items-center rounded-xl border-2 border-dashed p-8 text-center transition-all ${
                    drag
                      ? "border-accent-foreground bg-accent/20"
                      : "border-border/80 bg-background/50 hover:bg-card/70"
                  }`}
                >
                  <div className="max-w-md space-y-3">
                    <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-accent/30 text-accent-foreground shadow-xs">
                      <UploadCloud className="size-7" />
                    </span>
                    <div>
                      <h2 className="text-base font-bold text-primary">
                        Drag and drop your specification here
                      </h2>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Supports PDF, DOCX, or TXT · Up to 20 MB file size
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => input.current?.click()}
                      className="mt-2"
                    >
                      Browse local files
                    </Button>
                    <input
                      ref={input}
                      hidden
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={(e) => {
                        const chosen = e.target.files?.[0];
                        if (chosen) validate(chosen);
                      }}
                    />
                  </div>
                </div>

                {file && (
                  <div className="flex items-center justify-between rounded-xl border border-border/80 bg-card p-4">
                    <div className="flex items-center gap-3">
                      <span className="grid size-10 place-items-center rounded-lg bg-accent/20 text-accent-foreground">
                        <FileText className="size-5" />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-bold text-primary">{file.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {(file.size / (1024 * 1024)).toFixed(2)} MB · Ready for analysis
                        </p>
                      </div>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => setFile(null)}
                      aria-label="Remove selected file"
                    >
                      <X className="size-4" />
                    </Button>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="paste" className="mt-5 space-y-2">
                <Textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste specification requirements, tender clauses, BOQ items, or material parameters..."
                  className="min-h-60 resize-y rounded-xl font-mono text-xs leading-relaxed"
                  maxLength={30000}
                />
                <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
                  <span>Plain text or markdown</span>
                  <span className="font-mono">
                    {text.length.toLocaleString()} / 30,000 characters
                  </span>
                </div>
              </TabsContent>
            </Tabs>

            {error && (
              <div
                role="alert"
                className="flex items-center gap-2.5 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-xs font-semibold text-destructive"
              >
                <AlertCircle className="size-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex items-center justify-between border-t border-border/70 pt-6">
              <span className="text-xs text-muted-foreground">
                Engine: <strong className="text-primary font-mono">StandardOS v3.1</strong>
              </span>
              <Button size="lg" onClick={run} className="gap-2 shadow-xs">
                <span>Start Intelligence Analysis</span>
                <ArrowRight className="size-4" />
              </Button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function Processing({ progress }: { progress: number }) {
  const currentProgressPct = Math.min(100, Math.max(8, Math.round((progress / 8) * 100)));
  const activeStage = PIPELINE_STAGES[Math.min(progress, 7)];

  return (
    <section className="intel-card p-8 sm:p-10 space-y-8">
      <div>
        <div className="flex items-center justify-between">
          <p className="eyebrow flex items-center gap-2">
            <Cpu className="size-3.5" />
            <span>Analysis In Execution</span>
          </p>
          <span className="font-mono text-xs font-bold text-accent-foreground">
            Stage {Math.min(progress, 8)} of 8 · {currentProgressPct}%
          </span>
        </div>
        <h2 className="mt-2 text-2xl font-extrabold text-primary">
          {activeStage?.title ?? "Processing Specification"}
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          {activeStage?.desc ??
            "Tracing requirements and normative references in standards knowledge graph"}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full bg-accent-foreground transition-all duration-500 ease-out"
          style={{ width: `${currentProgressPct}%` }}
        />
      </div>

      {/* 8-Stage Precision Grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {PIPELINE_STAGES.map((stage, index) => {
          const done = index < progress;
          const active = index === progress;
          return (
            <div
              key={stage.id}
              className={`flex items-start gap-3 rounded-xl border p-3.5 transition-all ${
                done
                  ? "border-success/40 bg-success/5 text-primary"
                  : active
                    ? "border-accent-foreground/60 bg-accent/20 text-primary shadow-xs"
                    : "border-border/60 bg-background/30 opacity-40"
              }`}
            >
              <span
                className={`grid size-7 shrink-0 place-items-center rounded-lg text-xs font-bold ${
                  done
                    ? "bg-success text-success-foreground"
                    : active
                      ? "bg-accent-foreground text-background beacon"
                      : "border border-border text-muted-foreground"
                }`}
              >
                {done ? (
                  <Check className="size-3.5 stroke-[3]" />
                ) : active ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <span>{stage.id}</span>
                )}
              </span>
              <div className="min-w-0">
                <p className="text-xs font-bold">{stage.title}</p>
                <p className="text-[11px] text-muted-foreground truncate">{stage.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
