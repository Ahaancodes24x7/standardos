"""Integration tests run against a real Postgres named by TEST_DATABASE_URL.

    TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/standardos_test uv run pytest backend/tests

The database is migrated with Alembic and seeded with the bundled corpus.
Tests are skipped when TEST_DATABASE_URL is unset. Never point it at a
database whose data you want to keep.
"""

from __future__ import annotations

import os
import uuid

import pytest

TEST_URL = os.environ.get("TEST_DATABASE_URL")

if TEST_URL:
    # Must be set before app modules read settings; overrides any .env values.
    os.environ["DATABASE_URL"] = TEST_URL
    os.environ["DB_MIGRATION_URL"] = TEST_URL
    os.environ["SESSION_SECRET"] = "test-secret-" + "x" * 40
    os.environ["CRON_SECRET"] = "cron-test-secret"
    os.environ["STANDARDOS_LLM_REPAIR"] = "off"

pytestmark = pytest.mark.skipif(not TEST_URL, reason="TEST_DATABASE_URL is not set")


@pytest.fixture(scope="session")
def migrated() -> None:
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    backend = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend / "alembic"))
    command.upgrade(cfg, "head")

    from standardos_aiml.standards.seed import seed_corpus

    from app.corpus import import_corpus
    from app.db import session_scope

    with session_scope() as db:
        import_corpus(db, seed_corpus(), "curated-seed")


@pytest.fixture()
def client(migrated):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


def sign_up(client, name: str = "Reviewer") -> dict:
    email = f"{name.lower()}-{uuid.uuid4().hex[:10]}@example.com"
    res = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "correct horse battery", "fullName": name, "organization": "Test Cell"},
    )
    assert res.status_code == 200, res.text
    return {"email": email, **res.json()}
