import { Outlet } from "@tanstack/react-router";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { CommandPalette } from "@/components/layout/command-palette";
export function AppLayout(){return <div className="min-h-screen bg-background"><AppSidebar/><main className="min-h-screen pt-16 lg:ml-64 lg:pt-0"><div className="app-container py-8 lg:py-12"><Outlet/></div></main><CommandPalette/></div>}
