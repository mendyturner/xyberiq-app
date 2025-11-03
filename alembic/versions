"""initial schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


revision = "202511030001"
down_revision = None
branch_labels = None
depends_on = None


ROLE_KEY_ENUM = (
    "employee",
    "manager",
    "hr",
    "it",
    "admin",
)

USER_STATUS_ENUM = (
    "active",
    "inactive",
)

CONTROL_TYPE_ENUM = (
    "administrative",
    "technical",
    "physical",
)

CONTENT_TYPE_ENUM = (
    "video",
    "scorm",
    "pdf",
    "quiz",
    "simulation",
)

ASSIGNMENT_STATUS_ENUM = (
    "assigned",
    "in_progress",
    "completed",
    "overdue",
)

EVENT_TYPE_ENUM = (
    "phish_fail",
    "policy_ack",
    "login",
    "quiz_attempt",
    "content_view",
)

EXPORT_TYPE_ENUM = (
    "employees_csv",
    "assignments_csv",
    "evidence_zip",
)

EXPORT_STATUS_ENUM = (
    "pending",
    "processing",
    "ready",
    "failed",
)

POLICY_STATUS_ENUM = (
    "draft",
    "published",
    "archived",
)


def upgrade() -> None:
    bind = op.get_bind()

    sa.Enum(*ROLE_KEY_ENUM, name="role_key").create(bind, checkfirst=True)
    sa.Enum(*USER_STATUS_ENUM, name="user_status").create(bind, checkfirst=True)
    sa.Enum(*CONTROL_TYPE_ENUM, name="control_type").create(bind, checkfirst=True)
    sa.Enum(*CONTENT_TYPE_ENUM, name="content_type").create(bind, checkfirst=True)
    sa.Enum(*ASSIGNMENT_STATUS_ENUM, name="assignment_status").create(bind, checkfirst=True)
    sa.Enum(*EVENT_TYPE_ENUM, name="event_type").create(bind, checkfirst=True)
    sa.Enum(*EXPORT_TYPE_ENUM, name="export_type").create(bind, checkfirst=True)
    sa.Enum(*EXPORT_STATUS_ENUM, name="export_status").create(bind, checkfirst=True)
    sa.Enum(*POLICY_STATUS_ENUM, name="policy_status").create(bind, checkfirst=True)

    op.create_table(
        "tenants",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "compliance_frameworks",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("key", name="uq_frameworks_key"),
    )

    op.create_table(
        "controls",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("framework_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("control_key", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("control_type", sa.Enum(*CONTROL_TYPE_ENUM, name="control_type"), nullable=False),
        sa.Column("tags", pg.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["framework_id"], ["compliance_frameworks.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("framework_id", "control_key", name="uq_controls_framework_key"),
    )

    op.create_table(
        "modules",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("framework_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(length=50), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["framework_id"], ["compliance_frameworks.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="uq_modules_code"),
    )

    op.create_table(
        "training_content",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("module_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("uri", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.Enum(*CONTENT_TYPE_ENUM, name="content_type"), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("module_id", "version", name="uq_content_module_version"),
    )

    op.create_table(
        "roles",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.Enum(*ROLE_KEY_ENUM, name="role_key"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "key", name="uq_roles_tenant_key"),
    )

    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])

    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("status", sa.Enum(*USER_STATUS_ENUM, name="user_status"), nullable=False, server_default="active"),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("manager_user_id", pg.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "module_controls",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("module_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("control_id", pg.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["control_id"], ["controls.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("module_id", "control_id", name="uq_module_controls_unique"),
    )

    op.create_table(
        "user_roles",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", pg.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "user_id", "role_id", name="uq_user_roles_unique"),
    )

    op.create_index("ix_user_roles_tenant_id", "user_roles", ["tenant_id"])

    op.create_table(
        "assignments",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum(*ASSIGNMENT_STATUS_ENUM, name="assignment_status"), nullable=False, server_default="assigned"),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_by_user_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("retrain_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index("ix_assignments_tenant_id", "assignments", ["tenant_id"])
    op.create_index("ix_assignments_status", "assignments", ["status"])
    op.create_index("ix_assignments_due_date", "assignments", ["due_date"])

    op.create_table(
        "policies",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("uri", sa.String(length=1024), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum(*POLICY_STATUS_ENUM, name="policy_status"), nullable=False, server_default="draft"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "name", "version", name="uq_policies_tenant_name_version"),
    )

    op.create_index("ix_policies_tenant_id", "policies", ["tenant_id"])

    op.create_table(
        "policy_acknowledgements",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "policy_id", "user_id", name="uq_policy_ack_unique"),
    )

    op.create_index("ix_policy_acknowledgements_tenant_id", "policy_acknowledgements", ["tenant_id"])

    op.create_table(
        "events",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.Enum(*EVENT_TYPE_ENUM, name="event_type"), nullable=False),
        sa.Column("payload", pg.JSONB(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index("ix_events_tenant_id", "events", ["tenant_id"])
    op.create_index("ix_events_occurred_at", "events", ["occurred_at"])

    op.create_table(
        "assessments",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("answers", pg.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="SET NULL"),
    )

    op.create_index("ix_assessments_tenant_id", "assessments", ["tenant_id"])

    op.create_table(
        "exports",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Enum(*EXPORT_TYPE_ENUM, name="export_type"), nullable=False),
        sa.Column("status", sa.Enum(*EXPORT_STATUS_ENUM, name="export_status"), nullable=False, server_default="pending"),
        sa.Column("storage_uri", sa.String(length=1024), nullable=True),
        sa.Column("requested_by_user_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index("ix_exports_tenant_id", "exports", ["tenant_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("target_type", sa.String(length=255), nullable=True),
        sa.Column("target_id", sa.String(length=255), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=1024), nullable=True),
        sa.Column("meta", pg.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_exports_tenant_id", table_name="exports")
    op.drop_table("exports")
    op.drop_index("ix_assessments_tenant_id", table_name="assessments")
    op.drop_table("assessments")
    op.drop_index("ix_events_occurred_at", table_name="events")
    op.drop_index("ix_events_tenant_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_policy_acknowledgements_tenant_id", table_name="policy_acknowledgements")
    op.drop_table("policy_acknowledgements")
    op.drop_index("ix_policies_tenant_id", table_name="policies")
    op.drop_table("policies")
    op.drop_index("ix_assignments_due_date", table_name="assignments")
    op.drop_index("ix_assignments_status", table_name="assignments")
    op.drop_index("ix_assignments_tenant_id", table_name="assignments")
    op.drop_table("assignments")
    op.drop_index("ix_user_roles_tenant_id", table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_table("module_controls")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_roles_tenant_id", table_name="roles")
    op.drop_table("roles")
    op.drop_table("training_content")
    op.drop_table("modules")
    op.drop_table("controls")
    op.drop_table("compliance_frameworks")
    op.drop_table("tenants")

    bind = op.get_bind()
    sa.Enum(*POLICY_STATUS_ENUM, name="policy_status").drop(bind, checkfirst=True)
    sa.Enum(*EXPORT_STATUS_ENUM, name="export_status").drop(bind, checkfirst=True)
    sa.Enum(*EXPORT_TYPE_ENUM, name="export_type").drop(bind, checkfirst=True)
    sa.Enum(*EVENT_TYPE_ENUM, name="event_type").drop(bind, checkfirst=True)
    sa.Enum(*ASSIGNMENT_STATUS_ENUM, name="assignment_status").drop(bind, checkfirst=True)
    sa.Enum(*CONTENT_TYPE_ENUM, name="content_type").drop(bind, checkfirst=True)
    sa.Enum(*CONTROL_TYPE_ENUM, name="control_type").drop(bind, checkfirst=True)
    sa.Enum(*USER_STATUS_ENUM, name="user_status").drop(bind, checkfirst=True)
    sa.Enum(*ROLE_KEY_ENUM, name="role_key").drop(bind, checkfirst=True)
