"""initial_schema — full Knowledge Factory schema per architecture doc.

Revision ID: 001
Revises: None
Create Date: 2026-04-20

Creates all 12 core tables with:
- Multi-tenant design (tenant_id on all tables except tenants)
- Proper FK relationships with CASCADE/SET NULL semantics
- Indexes per architecture doc Section 5.2
- JSONB columns for flexible config/data
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── tenants ─────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("config_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    # ── users ────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("otp_secret", sa.String(32), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"])
    # Unique partial index: email per tenant (NULL tenant for SuperAdmin excluded from uniqueness)
    op.execute("""
        CREATE UNIQUE INDEX ix_users_email_per_tenant ON users (tenant_id, email)
        WHERE tenant_id IS NOT NULL
    """)

    # ── hiring_cycles ────────────────────────────────────────────────
    op.create_table(
        "hiring_cycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("eligibility_config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("assessment_config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("proctoring_config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_hiring_cycles_tenant_id", "hiring_cycles", ["tenant_id"])

    # ── candidates ──────────────────────────────────────────────────
    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cycle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hiring_cycles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("college", sa.String(255), nullable=False),
        sa.Column("branch", sa.String(50), nullable=False),
        sa.Column("cgpa", sa.Numeric(4, 2), nullable=False),
        sa.Column("passed_out_year", sa.Integer, nullable=False),
        sa.Column("resume_url", sa.String(500), nullable=True),
        sa.Column("govt_id_url", sa.String(500), nullable=True),
        sa.Column("language_choice", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="APPLIED"),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("custom_fields", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_candidates_tenant_id", "candidates", ["tenant_id"])
    op.create_index("ix_candidates_cycle_id", "candidates", ["cycle_id"])
    op.create_index("ix_candidates_email", "candidates", ["email"])
    op.create_index("ix_candidates_status", "candidates", ["status"])
    # Compound index per architecture doc Section 5.2
    op.create_index("ix_candidates_tenant_cycle_status", "candidates", ["tenant_id", "cycle_id", "status"])
    # Unique partial index: email per (tenant, cycle)
    op.execute("""
        CREATE UNIQUE INDEX ix_candidates_email_per_tenant_cycle ON candidates (tenant_id, cycle_id, email)
    """)

    # ── assessments ─────────────────────────────────────────────────
    op.create_table(
        "assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round", sa.String(10), nullable=False),
        sa.Column("questions_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("link_token", sa.String(64), nullable=False, unique=True),
        sa.Column("link_expiry", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="NOT_STARTED"),
        sa.Column("termination_reason", sa.Text, nullable=True),
    )
    op.create_index("ix_assessments_candidate_id", "assessments", ["candidate_id"])
    op.create_index("ix_assessments_link_token", "assessments", ["link_token"], unique=True)

    # ── submissions ─────────────────────────────────────────────────
    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section", sa.String(20), nullable=False),
        sa.Column("payload_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_submissions_assessment_id", "submissions", ["assessment_id"])

    # ── scores ──────────────────────────────────────────────────────
    op.create_table(
        "scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round", sa.String(10), nullable=False),
        sa.Column("correctness", sa.Integer, nullable=False),
        sa.Column("quality", sa.Integer, nullable=False),
        sa.Column("design", sa.Integer, nullable=False),
        sa.Column("edge_cases", sa.Integer, nullable=False),
        sa.Column("efficiency", sa.Integer, nullable=False),
        sa.Column("mcq_total", sa.Integer, nullable=False),
        sa.Column("weighted_total", sa.Numeric(5, 2), nullable=False),
        sa.Column("verdict", sa.String(10), nullable=False),
        sa.Column("feedback_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_scores_candidate_id", "scores", ["candidate_id"])

    # ── proctoring_records ─────────────────────────────────────────
    op.create_table(
        "proctoring_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("webcam_manifest_url", sa.String(500), nullable=True),
        sa.Column("screen_manifest_url", sa.String(500), nullable=True),
        sa.Column("govt_id_frame_url", sa.String(500), nullable=True),
        sa.Column("violations_json", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("warning_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("terminated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("retention_expiry", sa.Date, nullable=False),
    )
    op.create_index("ix_proctoring_records_assessment_id", "proctoring_records", ["assessment_id"], unique=True)
    op.create_index("ix_proctoring_records_candidate_id", "proctoring_records", ["candidate_id"])

    # ── interview_feedback ─────────────────────────────────────────
    op.create_table(
        "interview_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("technical", sa.Integer, nullable=False),
        sa.Column("problem_solving", sa.Integer, nullable=False),
        sa.Column("communication", sa.Integer, nullable=False),
        sa.Column("cultural_fit", sa.Integer, nullable=False),
        sa.Column("recommendation", sa.String(10), nullable=False),
        sa.Column("comments", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_interview_feedback_candidate_id", "interview_feedback", ["candidate_id"])

    # ── audit_logs ──────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("before_json", postgresql.JSONB, nullable=True),
        sa.Column("after_json", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    # BRIN index on created_at per architecture doc Section 5.2
    op.execute("CREATE INDEX ix_audit_logs_created_at_brin ON audit_logs USING BRIN (created_at)")

    # ── email_logs ──────────────────────────────────────────────────
    op.create_table(
        "email_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("template_name", sa.String(100), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("provider_message_id", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_email_logs_tenant_id", "email_logs", ["tenant_id"])
    op.create_index("ix_email_logs_recipient_email", "email_logs", ["recipient_email"])
    op.create_index("ix_email_logs_status", "email_logs", ["status"])

    # ── ai_generation_logs ─────────────────────────────────────────
    op.create_table(
        "ai_generation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False),
        sa.Column("output_tokens", sa.Integer, nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ai_generation_logs_tenant_id", "ai_generation_logs", ["tenant_id"])
    op.create_index("ix_ai_generation_logs_prompt_hash", "ai_generation_logs", ["prompt_hash"])
    op.create_index("ix_ai_generation_logs_status", "ai_generation_logs", ["status"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("ai_generation_logs")
    op.drop_table("email_logs")
    op.drop_table("audit_logs")
    op.drop_table("interview_feedback")
    op.drop_table("proctoring_records")
    op.drop_table("scores")
    op.drop_table("submissions")
    op.drop_table("assessments")
    op.drop_table("candidates")
    op.drop_table("hiring_cycles")
    op.drop_table("users")
    op.drop_table("tenants")
