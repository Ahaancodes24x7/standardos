"""StandardOS API — FastAPI application.

Run: ``uv run uvicorn app.main:app --reload --port 8000`` from ``backend/``.
Interactive docs at /api/docs.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from standardos_aiml.version import PIPELINE_VERSION

from .config import get_settings
from .corpus import get_corpus
from .db import DatabaseNotConfigured, database_configured
from .errors import AppError
from .routers import analyses, auth, insights, review, standards
from .security import SessionSecretMissing, cron_authorized
from .store import sweep_runs

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="StandardOS API",
    version="2.0.0",
    description="Procurement specification intelligence: requirement extraction, standards mapping, "
    "compliance reasoning, human review and audit.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse({"detail": exc.message}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:])
    message = first.get("msg", "Invalid request.")
    return JSONResponse({"detail": f"{field}: {message}" if field else message}, status_code=422)


@app.exception_handler(DatabaseNotConfigured)
async def no_database(_: Request, __: DatabaseNotConfigured) -> JSONResponse:
    return JSONResponse(
        {"detail": "The server has no database configured. Use the demo workspace or set DATABASE_URL."},
        status_code=503,
    )


@app.exception_handler(SessionSecretMissing)
async def no_secret(_: Request, exc: SessionSecretMissing) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=500)


app.include_router(auth.router)
app.include_router(analyses.router)
app.include_router(review.router)
app.include_router(standards.router)
app.include_router(insights.router)


@app.get("/api/health", tags=["system"])
def health():
    loaded = get_corpus()
    return {
        "ok": True,
        "pipelineVersion": PIPELINE_VERSION,
        "corpusVersion": loaded.corpus.version,
        "corpusSource": loaded.source,
        "database": database_configured(),
    }


@app.get("/api/cron/analysis-sweeper", tags=["system"])
def analysis_sweeper(authorization: str | None = Header(default=None)):
    status = cron_authorized(authorization)
    if status == 500:
        return JSONResponse({"detail": "Server configuration error"}, status_code=500)
    if status:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return sweep_runs()
