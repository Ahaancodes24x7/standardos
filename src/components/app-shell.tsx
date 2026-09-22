import { Link, useRouterState } from "@tanstack/react-router";
import { BookOpen, Languages, Menu, Search, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/search" as const, label: "Search" },
  { to: "/dashboard" as const, label: "Dashboard" },
  { to: "/about" as const, label: "Methodology" },
];

export function Wordmark() {
  return <span className="font-serif text-xl font-semibold text-primary">Standard<span className="text-accent-foreground">OS</span></span>;
}

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  return (
    <div className="min-h-screen">
      <header className="fixed inset-x-0 top-0 z-50 px-3 pt-3 sm:px-6 sm:pt-4">
        <div className="glass-panel mx-auto grid max-w-7xl grid-cols-[minmax(0,1fr)_auto] items-center px-4 py-3 sm:flex sm:px-5">
          <Link to="/" className="flex min-w-0 items-center gap-2.5" aria-label="StandardOS home">
            <span className="grid size-8 shrink-0 place-items-center rounded-sm bg-primary text-primary-foreground"><BookOpen className="size-4" /></span>
            <Wordmark />
          </Link>
          <nav className="ml-auto hidden items-center gap-1 md:flex" aria-label="Main navigation">
            {navItems.map((item) => <Link key={item.to} to={item.to} className="nav-link" activeProps={{ className: "nav-link nav-link-active" }}>{item.label}</Link>)}
            <span className="mx-2 h-5 w-px bg-border" />
            <Button variant="ghost" size="sm"><Languages /> EN</Button>
            <Button asChild size="sm"><Link to="/login">Sign in</Link></Button>
          </nav>
          <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setOpen((value) => !value)} aria-label="Toggle menu">
            {open ? <X /> : <Menu />}
          </Button>
          {open && <nav className="col-span-2 mt-3 grid gap-1 border-t border-border pt-3 md:hidden">
            {navItems.map((item) => <Link key={item.to} to={item.to} onClick={() => setOpen(false)} className={pathname === item.to ? "mobile-nav mobile-nav-active" : "mobile-nav"}>{item.label}</Link>)}
            <div className="mt-2 grid grid-cols-2 gap-2"><Button variant="outline"><Languages /> English</Button><Button asChild><Link to="/login">Sign in</Link></Button></div>
          </nav>}
        </div>
      </header>
      <main className="pt-24">{children}</main>
    </div>
  );
}

export function PageIntro({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <div className="grid gap-6 border-b border-border pb-8 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
    <div className="max-w-3xl"><p className="eyebrow">{eyebrow}</p><h1 className="mt-3 font-serif text-4xl leading-tight text-primary sm:text-5xl">{title}</h1><p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">{description}</p></div>{action}
  </div>;
}

export function SectionHeading({ eyebrow, title, description }: { eyebrow: string; title: string; description?: string }) {
  return <div className="max-w-2xl"><p className="eyebrow">{eyebrow}</p><h2 className="mt-3 font-serif text-3xl leading-tight text-primary sm:text-4xl">{title}</h2>{description && <p className="mt-3 leading-7 text-muted-foreground">{description}</p>}</div>;
}

export function EmptySearch() {
  return <div className="glass-panel grid min-h-72 place-items-center p-8 text-center"><div><Search className="mx-auto size-8 text-accent-foreground"/><h3 className="mt-4 font-serif text-2xl text-primary">Your evidence trail starts here</h3><p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">Describe a product, paste a tender clause, or upload a document to surface matching standards.</p></div></div>;
}