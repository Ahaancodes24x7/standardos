import { createFileRoute, redirect } from "@tanstack/react-router";
import { getCurrentUser } from "@/services/auth";
import { AppLayout } from "@/components/layout/app-layout";
import { hasDemoSession } from "@/contexts/auth-context";
export const Route = createFileRoute("/_authenticated")({
  ssr: false,
  beforeLoad: async ({ location }) => {
    if (hasDemoSession()) return;
    const user = await getCurrentUser().catch(() => null);
    if (!user) throw redirect({ to: "/login", search: { redirect: location.href } });
    return { user };
  },
  component: AppLayout,
});
