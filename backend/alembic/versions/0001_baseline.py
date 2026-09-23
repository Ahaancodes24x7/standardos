"""Baseline schema: accounts, standards knowledge graph, documents, runs, findings, repairs, audit.

The DDL is exactly the SQL of the two Drizzle migrations the TypeScript
backend used (alembic/sql/*.sql), so a database created by either backend has
the same schema. If the tables already exist (a database migrated by Drizzle),
the migration adopts them instead of failing.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-23
"""

from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
FILES = ["0001_accounts.sql", "0001_intelligence.sql"]
TABLES = [
    "audit_events",
    "repairs",
    "evidence",
    "findings",
    "requirement_standard_links",
    "requirements",
    "analysis_runs",
    "documents",
    "standard_prior_editions",
    "standard_version_events",
    "standard_relationships",
    "standard_clauses",
    "standards",
    "corpus_versions",
    "password_reset_tokens",
    "profiles",
    "users",
]


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if bind.dialect.server_version_info < (13,):  # gen_random_uuid() is built in from Postgres 13
        op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    for name in FILES:
        statements = (SQL_DIR / name).read_text(encoding="utf-8").split("--> statement-breakpoint")
        for statement in statements:
            sql = statement.strip()
            if not sql:
                continue
            if name == "0001_accounts.sql" and "users" in existing:
                continue
            if name == "0001_intelligence.sql" and "analysis_runs" in existing:
                continue
            op.execute(sql)


def downgrade() -> None:
    for table in TABLES:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
