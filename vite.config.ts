import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import tailwindcss from "@tailwindcss/vite";
import viteReact from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { nitro } from "nitro/vite";
import tsConfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  resolve: {
    dedupe: [
      "react",
      "react-dom",
      "react/jsx-runtime",
      "react/jsx-dev-runtime",
      "@tanstack/react-query",
      "@tanstack/query-core",
    ],
  },
  plugins: [
    tailwindcss(),
    tsConfigPaths({ projects: ["./tsconfig.json"] }),
    tanstackStart({
      // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
      server: { entry: "server" },
    }),
    // Nitro must come after tanstackStart() and before react() so Start's
    // server build is packaged into a deployable server (Vercel Functions,
    // Node, etc.) instead of a raw Vite SSR bundle nothing knows how to run.
    nitro({
      // On Vercel the /api gateway waits for POST /api/runs/{id}/execute, which runs the
      // pipeline synchronously; allow it the same 60 s as the API function.
      vercel: { functions: { maxDuration: 60 } },
    }),
    // react's vite plugin must come after start's vite plugin
    viteReact(),
  ],
});
