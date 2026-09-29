import { useNavigate, useRouterState } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Command,
  FileSearch,
  Files,
  FlaskConical,
  GitBranch,
  Landmark,
  Layers,
  PlayCircle,
  Scale,
  ShieldCheck,
  Sparkles,
  UserCog,
  Waypoints,
  Wrench,
  X,
} from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { consumeSignIn, setShowsOnSignIn, showsOnSignIn } from "./tour-state";

// ---------------------------------------------------------------------------
// Steps: each can open a page and spotlight an element on it ([data-tour=…] or a selector).
// ---------------------------------------------------------------------------

type Step = {
  id: string;
  title: string;
  icon: LucideIcon;
  body: string;
  points?: string[];
  tip?: string;
  route?:
    | "/dashboard"
    | "/analyze"
    | "/documents"
    | "/compliance"
    | "/standards"
    | "/changes"
    | "/evaluation";
  target?: string;
  visual?: "pipeline" | "workbench" | "finish";
};

const STEPS: Step[] = [
  {
    id: "welcome",
    title: "Welcome to StandardOS",
    icon: Sparkles,
    route: "/dashboard",
    visual: "pipeline",
    body: "StandardOS reads procurement documents the way a standards engineer would: it pulls out every requirement, finds the Indian Standard (IS / IS-IEC) that governs it, and tells you where the document conflicts with, omits or out-dates that standard — with the clause as evidence.",
    tip: "This tour opens each part of the site for you. Use → / ← or the buttons; Esc closes it.",
  },
  {
    id: "quick-actions",
    title: "Start from what you have",
    icon: Landmark,
    route: "/dashboard",
    target: "[data-tour='quick-actions']",
    body: "The quick actions open the analyser with the right document type already chosen — a CPWD / PWD / DISCOM / JJM tender, a bill of quantities, a vendor datasheet — or jump to clause-level standards search.",
  },
  {
    id: "kpis",
    title: "Your workspace at a glance",
    icon: BarChart3,
    route: "/dashboard",
    target: "[data-tour='kpis']",
    body: "Every figure is computed from your analysed documents and is clickable.",
    points: [
      "Open findings and high-severity issues to fix before the bid goes out",
      "IS standards your documents rely on, and requirements extracted",
      "Average readiness — a severity-weighted score per document",
    ],
  },
  {
    id: "network",
    title: "See how documents connect to standards",
    icon: GitBranch,
    route: "/dashboard",
    target: "[data-tour='network']",
    body: "Each line joins one of your documents to an Indian Standard its requirements map to. Green means the link is clean, amber means an open gap, red a conflict with the standard; square markers flag superseded editions.",
    tip: "Hover a document or standard to trace its links; click to open it.",
  },
  {
    id: "analyze",
    title: "Analyse any document",
    icon: FileSearch,
    route: "/analyze",
    target: "#document-type",
    body: "Upload a PDF, DOCX or TXT (up to 20 MB) or paste text. Choose what the document is — specification, tender, BOQ, datasheet, test or inspection report, or a type you name — so it is read correctly (a BOQ keeps its tables).",
    points: [
      "8 pipeline stages run in seconds: parsing, requirement extraction, classification, IS mapping, dependency reasoning, conformity, conflicts, repairs",
      "Commercial sections (ITB, GCC, EMD, BOQ headers) are recognised and not treated as technical requirements",
    ],
  },
  {
    id: "workbench",
    title: "Inside an analysis",
    icon: Layers,
    visual: "workbench",
    body: "Each analysed document opens in a workbench with its readiness score and four views. Every finding cites the requirement text and the standard clause it was checked against.",
    points: [
      "Compliance audit — conflicts, gaps, outdated IS editions, missing BIS/ISI conformity evidence",
      "Evidence graph — requirement → governing clause → standard → test method",
      "Specification repair — suggested replacement wording you accept, edit or reject",
      "Requirements — every extracted requirement with its category and mapped IS",
    ],
    tip: "Export Report downloads a compliance report of the document.",
  },
  {
    id: "documents",
    title: "Your document library",
    icon: Files,
    route: "/documents",
    target: "[data-tour='nav-documents']",
    body: "All analyses are stored in your workspace. Search, filter by status or document type, rename or re-type a document (it is re-analysed when that changes how it is read), or delete it with its audit trail.",
  },
  {
    id: "compliance",
    title: "Review findings — with an audit trail",
    icon: ShieldCheck,
    route: "/compliance",
    target: "[data-tour='nav-compliance']",
    body: "Findings from every document in one place. Open a finding to compare the requirement with the standard clause, then Confirm or Dismiss it with a note. Every decision is recorded with who made it and when.",
  },
  {
    id: "standards",
    title: "Explore the standards knowledge graph",
    icon: Waypoints,
    route: "/standards",
    target: "[data-tour='nav-standards']",
    body: "Browse the indexed Indian Standards, or switch to the interactive dependency DAG: which standards a standard requires (e.g. IS 456 → IS 269, IS 383, IS 1786), which test methods apply, and which editions are superseded.",
  },
  {
    id: "changes",
    title: "Know when a standard changes",
    icon: Scale,
    route: "/changes",
    target: "[data-tour='nav-changes']",
    body: "When an IS is amended, revised, superseded or withdrawn, StandardOS lists every document it affects — directly, or through a standard that depends on it (an IS 269 cement revision reaches specifications that only cite IS 456).",
  },
  {
    id: "evaluation",
    title: "How accurate is it?",
    icon: FlaskConical,
    route: "/evaluation",
    target: "[data-tour='nav-evaluation']",
    body: "The model evaluation page shows measured accuracy — requirement extraction, classification, standard mapping and findings — on versioned test sets, including blind ones, with 95% confidence intervals.",
  },
  {
    id: "command",
    title: "Get anywhere fast",
    icon: Command,
    target: "[data-tour='command']",
    body: "Press Ctrl + K (⌘ K on Mac) from any page to jump to a page or action.",
  },
  {
    id: "account",
    title: "Your account and the corpus",
    icon: UserCog,
    target: "[data-tour='account']",
    body: "Settings holds your profile and password. Corpus Admin shows the indexed standards; administrators can import a licensed standards corpus there. You can replay this tour from “Product tour” here at any time.",
  },
  {
    id: "finish",
    title: "You are ready",
    icon: PlayCircle,
    visual: "finish",
    body: "Analyse your first document now — a tender takes a few seconds. Findings are decision support for a qualified reviewer, not a certificate of compliance.",
  },
];

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

type TourApi = { start: (at?: string) => void };
const TourContext = createContext<TourApi>({ start: () => undefined });
export const useTour = () => useContext(TourContext);

export function TourProvider({ children }: { children: ReactNode }) {
  const { user, isDemo, loading } = useAuth();
  const identity = user?.id ?? (isDemo ? "demo" : null);
  const [index, setIndex] = useState<number | null>(null);

  // Open after every sign-in, unless this user switched it off.
  useEffect(() => {
    if (loading || !identity) return;
    if (consumeSignIn() && showsOnSignIn(identity)) setIndex(0);
  }, [identity, loading]);

  const api = useMemo<TourApi>(
    () => ({
      start: (at) =>
        setIndex(
          Math.max(
            0,
            STEPS.findIndex((s) => s.id === at),
          ),
        ),
    }),
    [],
  );

  return (
    <TourContext.Provider value={api}>
      {children}
      {index !== null && (
        <TourOverlay
          index={index}
          setIndex={setIndex}
          identity={identity}
          onClose={() => setIndex(null)}
        />
      )}
    </TourContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Overlay
// ---------------------------------------------------------------------------

type Rect = { top: number; left: number; width: number; height: number };
const PAD = 8;
const CARD_W = 400;

function findTarget(selector?: string): HTMLElement | null {
  if (!selector) return null;
  const el = document.querySelector<HTMLElement>(selector);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0 ? el : null;
}

function TourOverlay({
  index,
  setIndex,
  identity,
  onClose,
}: {
  index: number;
  setIndex: (i: number) => void;
  identity: string | null;
  onClose: () => void;
}) {
  const step = STEPS[index]!;
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [rect, setRect] = useState<Rect | null>(null);
  const [showOnSignIn, setShowOnSignIn] = useState(() =>
    identity ? showsOnSignIn(identity) : true,
  );
  const cardRef = useRef<HTMLDivElement>(null);

  // Open the step's page.
  useEffect(() => {
    if (step.route && pathname !== step.route) void navigate({ to: step.route });
  }, [step.route, pathname, navigate]);

  // Find and follow the spotlight target (it may render after navigation).
  useLayoutEffect(() => {
    let frame = 0;
    let tries = 0;
    let el: HTMLElement | null = null;
    const measure = () => {
      if (!el) return;
      const r = el.getBoundingClientRect();
      setRect({
        top: r.top - PAD,
        left: r.left - PAD,
        width: r.width + PAD * 2,
        height: r.height + PAD * 2,
      });
    };
    const locate = () => {
      el = findTarget(step.target);
      if (el) {
        el.scrollIntoView({ block: "center", behavior: "smooth" });
        window.setTimeout(measure, 350);
        measure();
      } else if (step.target && tries++ < 40) {
        frame = window.setTimeout(locate, 80);
      } else {
        setRect(null);
      }
    };
    setRect(null);
    locate();
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    return () => {
      window.clearTimeout(frame);
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure, true);
    };
  }, [step.target, step.id, pathname]);

  const close = useCallback(() => {
    if (identity) setShowsOnSignIn(identity, showOnSignIn);
    onClose();
  }, [identity, showOnSignIn, onClose]);
  const next = useCallback(
    () => (index < STEPS.length - 1 ? setIndex(index + 1) : close()),
    [index, setIndex, close],
  );
  const back = useCallback(() => index > 0 && setIndex(index - 1), [index, setIndex]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
      else if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") back();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [close, next, back]);

  useEffect(() => {
    cardRef.current?.focus();
  }, [index]);

  const cardStyle = placeCard(rect);
  const Icon = step.icon;
  const titleId = `tour-title-${step.id}`;

  return (
    <div className="fixed inset-0 z-[80]" aria-live="polite">
      {/* Dimmer with a cut-out around the target */}
      {rect ? (
        <div
          aria-hidden
          className="pointer-events-none fixed rounded-xl ring-2 ring-[var(--chart-saffron)] transition-all duration-300 ease-out"
          style={{
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
            boxShadow: "0 0 0 9999px rgba(10, 22, 40, 0.58)",
          }}
        />
      ) : (
        <div aria-hidden className="fixed inset-0 bg-[rgba(10,22,40,0.58)] backdrop-blur-[2px]" />
      )}
      {/* Clicks outside the card do nothing (the page behind is for show). */}
      <div className="fixed inset-0" onClick={(e) => e.stopPropagation()} />

      <div
        ref={cardRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="fixed flex max-h-[calc(100vh-2rem)] flex-col overflow-hidden rounded-2xl border border-border bg-background shadow-2xl outline-none transition-all duration-300"
        style={cardStyle}
      >
        <div className="h-1 w-full bg-muted">
          <div
            className="h-full bg-[var(--chart-saffron)] transition-all"
            style={{ width: `${((index + 1) / STEPS.length) * 100}%` }}
          />
        </div>
        <div className="overflow-y-auto p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-accent/40 text-accent-foreground">
                <Icon className="size-5" />
              </span>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
                  How StandardOS works · {index + 1} of {STEPS.length}
                </p>
                <h2 id={titleId} className="text-lg font-extrabold leading-tight text-primary">
                  {step.title}
                </h2>
              </div>
            </div>
            <button
              type="button"
              onClick={close}
              aria-label="Close tour"
              className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-primary"
            >
              <X className="size-4" />
            </button>
          </div>

          <p className="mt-3 text-sm leading-relaxed text-foreground/90">{step.body}</p>
          {step.visual === "pipeline" && <PipelineVisual />}
          {step.visual === "workbench" && <WorkbenchVisual />}
          {step.points && (
            <ul className="mt-3 space-y-1.5">
              {step.points.map((p) => (
                <li key={p} className="flex gap-2 text-[13px] leading-snug text-muted-foreground">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-[var(--chart-accent)]" />
                  {p}
                </li>
              ))}
            </ul>
          )}
          {step.tip && (
            <p className="mt-3 rounded-lg bg-muted/70 px-3 py-2 text-xs text-muted-foreground">
              {step.tip}
            </p>
          )}
          {step.visual === "finish" && (
            <div className="mt-4 grid gap-2">
              <Button
                className="justify-between"
                onClick={() => {
                  close();
                  void navigate({ to: "/analyze", search: { type: "tender" } });
                }}
              >
                Analyse a tender now <ArrowRight />
              </Button>
              <Button
                variant="outline"
                className="justify-between"
                onClick={() => {
                  close();
                  void navigate({ to: "/dashboard" });
                }}
              >
                Go to my dashboard <ArrowRight />
              </Button>
            </div>
          )}
        </div>

        <footer className="flex flex-wrap items-center gap-3 border-t border-border/70 bg-muted/50 px-5 py-3">
          <label className="flex cursor-pointer items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={showOnSignIn}
              onChange={(e) => setShowOnSignIn(e.target.checked)}
              className="size-3.5 accent-[var(--primary)]"
            />
            Show at every sign-in
          </label>
          <div className="ml-auto flex items-center gap-2">
            {index > 0 ? (
              <Button variant="ghost" size="sm" onClick={back}>
                <ArrowLeft /> Back
              </Button>
            ) : (
              <Button variant="ghost" size="sm" onClick={close}>
                Skip tour
              </Button>
            )}
            <Button size="sm" onClick={next}>
              {index === STEPS.length - 1 ? "Finish" : index === 0 ? "Start tour" : "Next"}
              {index < STEPS.length - 1 && <ArrowRight />}
            </Button>
          </div>
        </footer>
      </div>
    </div>
  );
}

/** Beside the target when it fits (sidebar items → right), else below / above, else centred. */
function placeCard(rect: Rect | null): CSSProperties {
  const vw = typeof window === "undefined" ? 1280 : window.innerWidth;
  const vh = typeof window === "undefined" ? 800 : window.innerHeight;
  const width = Math.min(CARD_W, vw - 32);
  if (!rect || vw < 640) {
    return {
      width,
      left: (vw - width) / 2,
      top: vw < 640 ? undefined : Math.max(16, vh * 0.12),
      bottom: vw < 640 ? 16 : undefined,
    };
  }
  const clampTop = (t: number) => Math.min(Math.max(16, t), Math.max(16, vh - 520));
  if (rect.left + rect.width + 16 + width <= vw - 16) {
    return { width, left: rect.left + rect.width + 16, top: clampTop(rect.top) };
  }
  const left = Math.min(Math.max(16, rect.left), vw - width - 16);
  if (rect.top + rect.height + 16 + 360 <= vh)
    return { width, left, top: rect.top + rect.height + 16 };
  if (rect.top - 16 - 360 >= 0) return { width, left, bottom: vh - rect.top + 16 };
  return { width, left: (vw - width) / 2, top: 16 };
}

// ---------------------------------------------------------------------------
// Visuals
// ---------------------------------------------------------------------------

const PIPELINE: Array<{ icon: LucideIcon; label: string; note: string }> = [
  { icon: FileSearch, label: "Upload", note: "PDF · DOCX · text" },
  { icon: Layers, label: "Extract", note: "requirements & values" },
  { icon: Waypoints, label: "Map", note: "to IS / IS-IEC clauses" },
  { icon: ShieldCheck, label: "Check", note: "conflicts · gaps · BIS" },
  { icon: Wrench, label: "Repair", note: "review & export" },
];

function PipelineVisual() {
  return (
    <ol className="mt-4 grid grid-cols-5 gap-1" aria-label="Analysis pipeline">
      {PIPELINE.map(({ icon: I, label, note }, i) => (
        <li key={label} className="relative flex flex-col items-center text-center">
          {i < PIPELINE.length - 1 && (
            <span
              aria-hidden
              className="absolute left-[calc(50%+18px)] right-[calc(-50%+18px)] top-[18px] h-px bg-border"
            />
          )}
          <span className="relative grid size-9 place-items-center rounded-full border border-border bg-background text-accent-foreground">
            <I className="size-4" />
          </span>
          <b className="mt-1.5 text-[11px] text-primary">{label}</b>
          <span className="text-[9.5px] leading-tight text-muted-foreground">{note}</span>
        </li>
      ))}
    </ol>
  );
}

function WorkbenchVisual() {
  return (
    <div className="mt-4 rounded-xl border border-border bg-background/70 p-3" aria-hidden>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[9px] font-bold uppercase tracking-wider text-muted-foreground">
            Example · Tender · CPWD
          </p>
          <p className="text-sm font-extrabold text-primary">LT distribution works</p>
        </div>
        <div className="text-right">
          <p className="text-xl font-extrabold text-[var(--chart-gap)]">69%</p>
          <p className="text-[9px] text-muted-foreground">readiness</p>
        </div>
      </div>
      <div className="mt-2 flex gap-1 text-[10px] font-semibold">
        {["Compliance audit", "Evidence graph", "Repair", "Requirements"].map((t, i) => (
          <span
            key={t}
            className={`rounded-md px-2 py-1 ${i === 0 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
          >
            {t}
          </span>
        ))}
      </div>
      <div className="mt-2 rounded-md border border-border/70 p-2 text-[11px]">
        <span className="rounded bg-destructive/15 px-1 font-bold text-destructive">CONFLICT</span>{" "}
        <b className="text-primary">Ambient 50 °C exceeds IS/IEC 61439-1 (40 °C)</b>
        <p className="mt-0.5 text-muted-foreground">
          Requirement 3.1 ↔ IS/IEC 61439-1:2020 · normal service conditions
        </p>
      </div>
    </div>
  );
}
