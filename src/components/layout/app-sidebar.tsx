import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import {
  BarChart3,
  BookOpen,
  Database,
  FileSearch,
  Files,
  FlaskConical,
  HelpCircle,
  LogOut,
  Menu,
  Scale,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Waypoints,
} from "lucide-react";
import { Brand } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useAuth } from "@/contexts/auth-context";

const navSections = [
  {
    title: "Workspace",
    items: [
      { to: "/dashboard", label: "Overview", icon: BarChart3 },
      { to: "/analyze", label: "Analyze Specification", icon: FileSearch },
      { to: "/documents", label: "Document Library", icon: Files },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { to: "/standards", label: "Standards & DAG", icon: Waypoints },
      { to: "/compliance", label: "Compliance Audit", icon: ShieldCheck },
      { to: "/changes", label: "Change Impact", icon: Scale },
    ],
  },
  {
    title: "Engine & Science",
    items: [{ to: "/evaluation", label: "Model Evaluation", icon: FlaskConical }],
  },
] as const;

function SidebarContent() {
  const path = useRouterState({ select: (state) => state.location.pathname });
  const { profile, isDemo, signOut } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col">
      {/* Brand & System Status */}
      <div>
        <Brand />
        <div className="mt-3.5 flex items-center justify-between rounded-lg border border-border/70 bg-card/60 px-2.5 py-1.5 text-[10px]">
          <span className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-muted-foreground">
            <span className="beacon inline-block size-1.5 rounded-full bg-success-foreground" />
            <span>BIS v3.1 Engine</span>
          </span>
          <span className="rounded bg-accent/40 px-1.5 py-0.5 font-mono text-[9px] font-bold text-accent-foreground">
            {isDemo ? "DEMO" : "LIVE"}
          </span>
        </div>
      </div>

      {/* Global Quick Search Shortcut */}
      <button
        type="button"
        onClick={() => {
          const event = new KeyboardEvent("keydown", { key: "k", metaKey: true, ctrlKey: true });
          window.dispatchEvent(event);
        }}
        className="mt-4 flex w-full items-center justify-between rounded-lg border border-border/80 bg-background/60 px-3 py-2 text-xs text-muted-foreground transition hover:border-accent-foreground/50 hover:bg-card hover:text-foreground"
      >
        <span className="flex items-center gap-2">
          <Search className="size-3.5 text-accent-foreground" />
          <span>Quick command...</span>
        </span>
        <kbd className="rounded border border-border bg-muted/60 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
          ⌘K
        </kbd>
      </button>

      {/* Structured Navigation Groups */}
      <nav className="mt-5 flex-1 space-y-5 overflow-y-auto pr-1" aria-label="Workspace">
        {navSections.map((section) => (
          <div key={section.title}>
            <p className="px-2 text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground/80">
              {section.title}
            </p>
            <div className="mt-1.5 grid gap-0.5">
              {section.items.map(({ to, label, icon: Icon }) => {
                const active = path === to || (to !== "/dashboard" && path.startsWith(`${to}/`));
                return (
                  <Link
                    key={to}
                    to={to}
                    className={`flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-semibold transition-all ${
                      active
                        ? "bg-accent/40 text-primary shadow-xs font-bold"
                        : "text-muted-foreground hover:bg-accent/20 hover:text-primary"
                    }`}
                  >
                    <Icon
                      className={`size-4 ${active ? "text-accent-foreground" : "text-muted-foreground"}`}
                    />
                    <span>{label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer Navigation */}
      <div className="mt-auto border-t border-border/80 pt-3">
        <div className="grid gap-0.5">
          <Link
            to="/admin"
            className={`flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent/20 hover:text-primary ${
              path === "/admin" ? "bg-accent/30 font-semibold text-primary" : ""
            }`}
          >
            <Database className="size-3.5" />
            <span>Corpus Admin</span>
          </Link>
          <Link
            to="/settings"
            className={`flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent/20 hover:text-primary ${
              path === "/settings" ? "bg-accent/30 font-semibold text-primary" : ""
            }`}
          >
            <Settings className="size-3.5" />
            <span>Settings</span>
          </Link>
          <a
            href="mailto:support@standardos.in"
            className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent/20 hover:text-primary"
          >
            <HelpCircle className="size-3.5" />
            <span>Support</span>
          </a>
        </div>

        {/* User Card */}
        <div className="mt-3 flex items-center gap-2.5 rounded-xl border border-border/70 bg-card/70 p-2">
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary font-mono text-xs font-bold text-primary-foreground shadow-xs">
            {profile?.full_name
              ?.split(" ")
              .map((word) => word[0])
              .slice(0, 2)
              .join("") || "SO"}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-bold text-primary">
              {profile?.full_name ?? "Workspace User"}
            </p>
            <p className="truncate text-[10px] text-muted-foreground">
              {profile?.organization ?? "STANDARDOS"}
            </p>
          </div>
          <Button
            size="icon"
            variant="ghost"
            className="size-7 text-muted-foreground hover:text-destructive"
            aria-label="Log out"
            title="Log out"
            onClick={async () => {
              await signOut();
              void navigate({ to: "/login", replace: true });
            }}
          >
            <LogOut className="size-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export function AppSidebar() {
  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-border/80 bg-sidebar/95 p-4 backdrop-blur-xl lg:block">
        <SidebarContent />
      </aside>
      <div className="fixed inset-x-0 top-0 z-30 flex h-14 items-center justify-between border-b border-border/80 bg-background/90 px-4 backdrop-blur-xl lg:hidden">
        <Brand />
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Open workspace navigation">
              <Menu className="size-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[84%] max-w-xs p-5">
            <SheetTitle className="sr-only">Workspace navigation</SheetTitle>
            <SidebarContent />
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
