"""Document types: any procurement document (specification, tender, BOQ, datasheet, report, other).

Revision ID: 0002_document_types
Revises: 0001_baseline
Create Date: 2026-09-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_document_types"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

TYPES = ("specification", "tender", "boq", "datasheet", "test_report", "inspection_report", "other")


def upgrade() -> None:
    op.add_column("documents", sa.Column("document_type", sa.Text(), nullable=False, server_default="specification"))
    op.add_column("documents", sa.Column("document_type_label", sa.Text(), nullable=True))
    op.create_check_constraint(
        "documents_document_type_valid",
        "documents",
        "document_type IN (" + ", ".join(f"'{t}'" for t in TYPES) + ")",
    )
    op.create_check_constraint(
        "documents_document_type_label_length",
        "documents",
        "document_type_label IS NULL OR char_length(document_type_label) BETWEEN 1 AND 60",
    )
    op.create_index("documents_owner_type_idx", "documents", ["owner_id", "document_type"])


def downgrade() -> None:
    op.drop_index("documents_owner_type_idx", table_name="documents")
    op.drop_constraint("documents_document_type_label_length", "documents", type_="check")
    op.drop_constraint("documents_document_type_valid", "documents", type_="check")
    op.drop_column("documents", "document_type_label")
    op.drop_column("documents", "document_type")
