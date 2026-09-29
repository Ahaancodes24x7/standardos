import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
import { markSignIn } from "./components/tour/tour-state";

const AUTH_PATHS = new Set(["/login", "/signup"]);

export const getRouter = () => {
  const queryClient = new QueryClient();

  const router = createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    defaultPreloadStaleTime: 0,
  });

  // A move from the sign-in / sign-up screens into the app is a fresh sign-in: queue the
  // product tour (components/tour/product-tour.tsx shows it once the workspace renders).
  if (typeof window !== "undefined") {
    router.subscribe("onBeforeNavigate", ({ fromLocation, toLocation }) => {
      const from = fromLocation?.pathname ?? "";
      if (AUTH_PATHS.has(from) && !AUTH_PATHS.has(toLocation.pathname)) markSignIn();
    });
  }

  return router;
};
