# Deploying StandardOS on Vercel

StandardOS is two Vercel projects from the same repository plus a Postgres database:

| Project | Root Directory | What it serves |
| --- | --- | --- |
| **web** | `/` (repository root) | TanStack Start app built by Nitro (Vercel preset). Its `/api/*` route is a same-origin gateway that forwards to the API. |
| **api** | `deploy/vercel-api` | FastAPI as one Python function (`api/index.py`) with the engine bundled next to it. |
| database | — | Postgres (e.g. Neon). Use the **pooled** connection string. |

Why two projects: the web project is built by Nitro into Vercel's Build Output, which
does not also build Python functions, and a Python function only sees its own Root
Directory. `deploy/vercel-api` therefore contains a copy of `backend/app` and
`aiml/standardos_aiml`, produced by `backend/scripts/build_vercel_api.py`;
`backend/tests/test_vercel_bundle.py` fails whenever the copy is out of date.

## Why an analysis could be accepted but never show a result

Two things caused the symptom and both are fixed:

1. **No API behind the gateway.** With only the web project deployed, the gateway
   forwarded to `http://127.0.0.1:8000`, which does not exist in a Vercel function. The
   gateway now answers `503` with *"The StandardOS API is not configured for this
   deployment…"* until `API_INTERNAL_URL` is set, and the client reports gateway
   errors instead of polling for five minutes.
2. **Work after the response is frozen on serverless.** The API used to run the
   pipeline in a background task after answering `POST /api/analyses`; Vercel freezes
   a function once its response is sent, so the run stayed `queued`/`running`. On
   Vercel (`VERCEL=1`) the API no longer schedules background work: the client calls
   the idempotent `POST /api/runs/{id}/execute`, re-calls it if a run stops making
   progress, and a run whose heartbeat is older than 90 s is reclaimed. A daily cron
   (`/api/cron/analysis-sweeper`) finishes anything a closed browser left behind.

## 1. Database

Create a Postgres database and run the migrations **from your machine** (the functions never migrate):

```bash
cd backend
# Point BOTH variables at the database you mean to migrate — .env may point elsewhere.
export DATABASE_URL="postgresql://…"      # pooled URL (Neon: host contains -pooler)
export DB_MIGRATION_URL="postgresql://…"  # direct URL
uv run alembic upgrade head
uv run python -m scripts.seed_standards
```

## 2. API project (`deploy/vercel-api`)

1. Vercel → New Project → import the repository → **Root Directory: `deploy/vercel-api`**,
   Framework Preset: *Other*. `vercel.json` routes every path to `api/index.py`
   (Python 3.12, 60 s max duration).
2. Environment variables:

   | Variable | Value |
   | --- | --- |
   | `DATABASE_URL` | pooled Postgres URL |
   | `SESSION_SECRET` | 32+ random characters |
   | `SESSION_COOKIE_SECURE` | `true` |
   | `CRON_SECRET` | random string (Vercel Cron sends it as a bearer token) |
   | `STANDARDOS_PIPELINE_CONFIG` | `v3.1` (default) |
   | `ADMIN_EMAILS` | e-mails allowed to import a standards corpus (optional) |

3. Deploy, then check `https://<api-project>.vercel.app/api/health` returns
   `"ok": true` and `"database": true`.

Keep the API reachable from the web project: if Vercel Deployment Protection is on
for the API project, exempt the production domain (the gateway calls it server-to-server).

## 3. Web project (repository root)

1. Vercel → New Project → same repository → Root Directory `/`. Nitro detects Vercel
   and emits `.vercel/output` (the gateway function gets a 60 s max duration).
2. Environment variable: `API_INTERNAL_URL=https://<api-project>.vercel.app`.
3. Deploy. Sign up, analyse a document: the result page opens when the run finishes.

## Updating

After changing `backend/app` or `aiml/standardos_aiml`:

```bash
cd backend && uv run python -m scripts.build_vercel_api   # refresh deploy/vercel-api
uv run pytest                                              # includes the bundle check
```

Commit `deploy/vercel-api` with the change; both projects redeploy from the push.

## Verified locally

The bundle was run exactly as Vercel runs it: a fresh virtualenv with only
`deploy/vercel-api/requirements.txt`, `api/index.py` served with `VERCEL=1`, and the
production web build served with `VERCEL=1 API_INTERNAL_URL=…`. A browser walk-through
(sign-up, tender / BOQ / custom-type analyses, library filter, edit + re-analysis,
delete, demo workspace) passed with no console errors. `NITRO_PRESET=vercel` builds a
valid `.vercel/output` (`__server` function, `maxDuration: 60`).
