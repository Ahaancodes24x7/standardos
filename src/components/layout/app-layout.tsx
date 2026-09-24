import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { CommandPalette } from "@/components/layout/command-palette";
import { ChevronRight, FileSearch, Search, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

const ROUTE_LABELS: Record<string, string> = {
  dashboard: "Workspace Overview",
  analyze: "Analyze Specification",
  documents: "Document Library",
  standards: "Standards & DAG",
  compliance: "Compliance Findings",
  changes: "Change Impact",
  evaluation: "Model Evaluation",
  settings: "Workspace Settings",
  admin: "Corpus Administration",
};

export function AppLayout() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const segments = pathname.split("/").filter(Boolean);
  const currentKey = segments[0] || "dashboard";
  const currentLabel = ROUTE_LABELS[currentKey] ?? "Workspace";

  return (
    <div className="min-h-screen bg-background">
      <AppSidebar />
      <div className="min-h-screen lg:ml-64 flex flex-col">
        {/* Desktop Top Utility Bar */}
        <header className="sticky top-0 z-20 hidden h-14 items-center justify-between border-b border-border/70 bg-background/85 px-6 backdrop-blur-xl lg:flex">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="font-semibold text-primary">StandardOS</span>
            <ChevronRight className="size-3.5 text-muted-foreground/60" />
            <span className="font-bold text-primary">{currentLabel}</span>
            {segments[1] && (
              <>
                <ChevronRight className="size-3.5 text-muted-foreground/60" />
                <span className="truncate max-w-[200px] font-mono text-[11px] text-muted-foreground">
                  {segments[1]}
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                const event = new KeyboardEvent("keydown", {
                  key: "k",
                  metaKey: true,
                  ctrlKey: true,
                });
                window.dispatchEvent(event);
              }}
              className="flex items-center gap-2 rounded-lg border border-border/80 bg-muted/30 px-3 py-1.5 text-xs text-muted-foreground transition hover:border-accent-foreground/50 hover:bg-card"
            >
              <Search className="size-3.5 text-accent-foreground" />
              <span>Search commands & standards...</span>
              <kbd className="rounded border border-border bg-background px-1.5 py-0.5 font-mono text-[10px]">
                ⌘K
              </kbd>
            </button>

            {pathname !== "/analyze" && (
              <Button asChild size="sm" className="h-8 gap-1.5 text-xs">
                <Link to="/analyze">
                  <FileSearch className="size-3.5" />
                  <span>Analyze</span>
                </Link>
              </Button>
            )}
          </div>
        </header>

        {/* Main Page Canvas */}
        <main className="flex-1 pt-14 lg:pt-0">
          <div className="app-container py-6 sm:py-8 lg:py-10">
            <Outlet />
          </div>
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
