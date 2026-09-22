# STANDARDOS

**From Specifications to Certainty.**

STANDARDOS is a standards intelligence platform for procurement and compliance teams. It analyzes procurement specifications and tender documents, maps the applicable Indian Standards (BIS), detects compliance gaps and conflicts, and generates evidence-backed corrections — with clause-level citations back to the source standard.

## Tech stack

- [TanStack Start](https://tanstack.com/start) (React 19, file-based routing, SSR)
- [Supabase](https://supabase.com) (auth, Postgres, storage)
- [Drizzle ORM](https://orm.drizzle.team) for schema/migrations
- Tailwind CSS v4
- Vite

## Getting started

Requires [Bun](https://bun.sh).

```sh
bun install
bun run dev
```

The app runs at `http://localhost:3000` by default.

### Environment variables

Copy `.env` and fill in your own Supabase project values:

```
SUPABASE_PROJECT_ID=
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SERVICE_ROLE_KEY=
VITE_SUPABASE_PROJECT_ID=
VITE_SUPABASE_URL=
VITE_SUPABASE_PUBLISHABLE_KEY=
```

Server-side jobs and migrations additionally use `CRON_SECRET` / `CRON_SECRET_PREVIOUS` (scheduled request auth) and `DB_MIGRATION_URL` (Drizzle migrations).

## Scripts

| Command | Description |
| --- | --- |
| `bun run dev` | Start the dev server |
| `bun run build` | Production build |
| `bun run preview` | Preview the production build locally |
| `bun run lint` | Run ESLint |
| `bun run format` | Format the codebase with Prettier |
