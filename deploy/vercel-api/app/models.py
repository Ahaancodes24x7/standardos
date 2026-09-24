"""ORM models.

Relational tables hold both the per-analysis results and the standards
knowledge graph. Structured sub-objects that are always read with their parent
row (quantities, provenance, checklist items) are stored as jsonb in the same
camelCase shape the API returns. Table, column and constraint names are
unchanged from the previous Drizzle schema, so existing databases keep working.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

REAL = Float(precision=24)  # Postgres "real"


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))


def _ts(nullable: bool = True, default_now: bool = False) -> Mapped[Any]:
    return mapped_column(
        DateTime(timezone=True), nullable=nullable, server_default=func.now() if default_now else None
    )


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = _ts(False, True)


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("char_length(full_name) BETWEEN 1 AND 100", name="full_name_length"),
        CheckConstraint("char_length(organization) BETWEEN 1 AND 160", name="organization_length"),
    )
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    organization: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = _ts(False, True)
    updated_at: Mapped[datetime] = _ts(False, True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = _ts(False)
    used_at: Mapped[Optional[datetime]] = _ts()
    created_at: Mapped[datetime] = _ts(False, True)


# ---------------------------------------------------------------------------
# Standards knowledge layer
# ---------------------------------------------------------------------------


class CorpusVersion(Base):
    __tablename__ = "corpus_versions"
    version: Mapped[str] = mapped_column(Text, primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    standard_count: Mapped[int] = mapped_column(Integer, nullable=False)
    relationship_count: Mapped[int] = mapped_column(Integer, nullable=False)
    loaded_at: Mapped[datetime] = _ts(False, True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))


class Standard(Base):
    __tablename__ = "standards"
    __table_args__ = (Index("standards_designation_idx", "designation"),)
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    designation: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    number: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    aliases: Mapped[list] = mapped_column(JSONB, nullable=False)
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False)
    certification: Mapped[dict] = mapped_column(JSONB, nullable=False)
    checklist: Mapped[list] = mapped_column(JSONB, nullable=False)
    source: Mapped[dict] = mapped_column(JSONB, nullable=False)
    corpus_version: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = _ts(False, True)


class StandardClause(Base):
    __tablename__ = "standard_clauses"
    __table_args__ = (Index("standard_clauses_standard_idx", "standard_id"),)
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    standard_id: Mapped[str] = mapped_column(Text, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    ref: Mapped[Optional[str]] = mapped_column(Text)
    heading: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    constraints: Mapped[list] = mapped_column(JSONB, nullable=False)


class StandardRelationship(Base):
    """Typed edges of the standards graph (REFERENCES, REQUIRES, TESTED_BY, SUPERSEDES, …)."""

    __tablename__ = "standard_relationships"
    __table_args__ = (
        Index("standard_rel_from_idx", "from_standard_id"),
        Index("standard_rel_to_idx", "to_standard_id"),
    )
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    from_standard_id: Mapped[str] = mapped_column(
        Text, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False
    )
    to_standard_id: Mapped[str] = mapped_column(Text, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    clause_id: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(REAL, nullable=False)
    method: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)


class StandardVersionEvent(Base):
    __tablename__ = "standard_version_events"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    standard_id: Mapped[str] = mapped_column(Text, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[Optional[str]] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    replaced_by_id: Mapped[Optional[str]] = mapped_column(Text)
    recorded_at: Mapped[datetime] = _ts(False, True)


class StandardPriorEdition(Base):
    __tablename__ = "standard_prior_editions"
    id: Mapped[uuid.UUID] = _uuid_pk()
    designation: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    replaced_by_id: Mapped[str] = mapped_column(Text, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)


# ---------------------------------------------------------------------------
# Documents and analysis runs
# ---------------------------------------------------------------------------


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index("documents_owner_idx", "owner_id"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    organization: Mapped[str] = mapped_column(Text, nullable=False)
    source_format: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(Text)
    mime_type: Mapped[Optional[str]] = mapped_column(Text)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    # What the document is (see app.doctypes); "other" carries a user-given label.
    document_type: Mapped[str] = mapped_column(Text, nullable=False, server_default="specification")
    document_type_label: Mapped[Optional[str]] = mapped_column(Text)
    # Original upload, kept so a run can be reproduced with a newer pipeline.
    original: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = _ts(False, True)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        Index("analysis_runs_document_idx", "document_id"),
        Index("analysis_runs_status_idx", "status"),
    )
    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'queued'"))  # queued|running|succeeded|failed
    stage: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    stage_name: Mapped[Optional[str]] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    error: Mapped[Optional[str]] = mapped_column(Text)
    error_code: Mapped[Optional[str]] = mapped_column(Text)
    pipeline_version: Mapped[Optional[str]] = mapped_column(Text)
    corpus_version: Mapped[Optional[str]] = mapped_column(Text)
    llm_model: Mapped[Optional[str]] = mapped_column(Text)
    parser: Mapped[Optional[str]] = mapped_column(Text)
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    warnings: Mapped[Optional[list]] = mapped_column(JSONB)
    readiness: Mapped[Optional[int]] = mapped_column(Integer)
    readiness_detail: Mapped[Optional[dict]] = mapped_column(JSONB)
    applicable_standard_ids: Mapped[Optional[list]] = mapped_column(JSONB)
    graph: Mapped[Optional[dict]] = mapped_column(JSONB)
    timings: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _ts(False, True)
    started_at: Mapped[Optional[datetime]] = _ts()
    heartbeat_at: Mapped[Optional[datetime]] = _ts()
    finished_at: Mapped[Optional[datetime]] = _ts()


class Requirement(Base):
    __tablename__ = "requirements"
    __table_args__ = (Index("requirements_run_idx", "run_id"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    local_id: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    span_start: Mapped[int] = mapped_column(Integer, nullable=False)
    span_end: Mapped[int] = mapped_column(Integer, nullable=False)
    page: Mapped[Optional[int]] = mapped_column(Integer)
    section_label: Mapped[Optional[str]] = mapped_column(Text)
    modality: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    category_scores: Mapped[dict] = mapped_column(JSONB, nullable=False)
    attributes: Mapped[list] = mapped_column(JSONB, nullable=False)
    quantities: Mapped[list] = mapped_column(JSONB, nullable=False)
    references: Mapped[list] = mapped_column(JSONB, nullable=False)
    entities: Mapped[list] = mapped_column(JSONB, nullable=False)
    terms: Mapped[list] = mapped_column(JSONB, nullable=False)
    vague: Mapped[bool] = mapped_column(Boolean, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False)


class RequirementStandardLink(Base):
    """Requirement → standard/clause mappings with rank, confidence and basis."""

    __tablename__ = "requirement_standard_links"
    __table_args__ = (
        Index("req_std_links_run_idx", "run_id"),
        Index("req_std_links_standard_idx", "standard_id"),
    )
    id: Mapped[uuid.UUID] = _uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    standard_id: Mapped[str] = mapped_column(Text, nullable=False)
    clause_id: Mapped[str] = mapped_column(Text, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(REAL, nullable=False)
    confidence: Mapped[float] = mapped_column(REAL, nullable=False)
    basis: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False)


# ---------------------------------------------------------------------------
# Findings, evidence, repairs, review and audit
# ---------------------------------------------------------------------------


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (Index("findings_run_idx", "run_id"), Index("findings_document_idx", "document_id"))
    id: Mapped[uuid.UUID] = _uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    local_id: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    rule: Mapped[str] = mapped_column(Text, nullable=False)
    parameter: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_local_id: Mapped[Optional[str]] = mapped_column(Text)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    standard_id: Mapped[Optional[str]] = mapped_column(Text)
    clause_id: Mapped[Optional[str]] = mapped_column(Text)
    standard_label: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # open | confirmed | dismissed — the reviewer's judgement of the finding.
    review_status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'open'"))
    review_note: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[Optional[datetime]] = _ts()


class EvidenceRow(Base):
    __tablename__ = "evidence"
    __table_args__ = (Index("evidence_finding_idx", "finding_id"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_local_id: Mapped[Optional[str]] = mapped_column(Text)
    span_start: Mapped[Optional[int]] = mapped_column(Integer)
    span_end: Mapped[Optional[int]] = mapped_column(Integer)
    standard_id: Mapped[Optional[str]] = mapped_column(Text)
    clause_id: Mapped[Optional[str]] = mapped_column(Text)
    relationship_ids: Mapped[Optional[list]] = mapped_column(JSONB)


class Repair(Base):
    __tablename__ = "repairs"
    __table_args__ = (Index("repairs_run_idx", "run_id"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False
    )
    local_id: Mapped[str] = mapped_column(Text, nullable=False)
    original: Mapped[str] = mapped_column(Text, nullable=False)
    recommended: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_label: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # pending | accepted | rejected | edited — AI proposes, a human decides.
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    final_text: Mapped[Optional[str]] = mapped_column(Text)
    decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    decided_at: Mapped[Optional[datetime]] = _ts()


class AuditEvent(Base):
    """Append-only log of human decisions and system events on analysis objects."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("audit_events_document_idx", "document_id"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE")
    )
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)  # document | run | finding | repair
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    before: Mapped[Optional[Any]] = mapped_column(JSONB)
    after: Mapped[Optional[Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _ts(False, True)
