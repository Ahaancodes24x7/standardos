"""SQLAlchemy engine and session factory (psycopg 3 driver)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


class DatabaseNotConfigured(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    if not settings.database_url:
        raise DatabaseNotConfigured("DATABASE_URL is not set.")
    if settings.is_serverless:
        # One short-lived instance per request burst: no pool to leak connections from.
        # Use the provider's pooled endpoint (e.g. Neon "-pooler") in DATABASE_URL.
        from sqlalchemy.pool import NullPool

        return create_engine(settings.database_url, poolclass=NullPool)
    return create_engine(
        settings.database_url,
        pool_size=settings.database_pool_max,
        max_overflow=0,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def database_configured() -> bool:
    return bool(get_settings().database_url)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with _session_factory()() as session:
        yield session


@contextmanager
def session_scope() -> Iterator[Session]:
    """A session for background work (job execution, sweeper, scripts)."""
    with _session_factory()() as session:
        yield session
