"""SQLAlchemy ORM models for the xyberiq training platform."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import (
    AssignmentStatus,
    ContentType,
    ControlType,
    EventType,
    ExportStatus,
    ExportType,
    PolicyStatus,
    RoleKey,
    UserStatus,
)
from app.db.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a customer tenant."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    billing_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    billing_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subscription_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    plan_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roles: Mapped[list["Role"]] = relationship("Role", back_populates="tenant", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="tenant", cascade="all, delete-orphan"
    )


class ComplianceFramework(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Compliance framework catalog (e.g. SOC2, ISO27001)."""

    __tablename__ = "compliance_frameworks"

    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    controls: Mapped[list["Control"]] = relationship("Control", back_populates="framework", cascade="all, delete")


class Control(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Control belonging to a compliance framework."""

    __tablename__ = "controls"

    framework_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("compliance_frameworks.id"), nullable=False)
    control_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    control_type: Mapped[ControlType] = mapped_column(
        Enum(ControlType, name="control_type", metadata=Base.metadata, native_enum=False), nullable=False
    )
    tags: Mapped[dict | None] = mapped_column(pg.JSONB, nullable=True)

    framework: Mapped["ComplianceFramework"] = relationship("ComplianceFramework", back_populates="controls")
    modules: Mapped[list["ModuleControl"]] = relationship(
        "ModuleControl", back_populates="control", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("framework_id", "control_key", name="uq_controls_framework_key"),)


class Module(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Training module available in the catalog."""

    __tablename__ = "modules"

    framework_id: Mapped[uuid.UUID | None] = mapped_column(
        pg.UUID(as_uuid=True), ForeignKey("compliance_frameworks.id"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(nullable=True)

    framework: Mapped["ComplianceFramework | None"] = relationship("ComplianceFramework", back_populates="modules")
    contents: Mapped[list["TrainingContent"]] = relationship(
        "TrainingContent", back_populates="module", cascade="all, delete-orphan"
    )
    controls: Mapped[list["ModuleControl"]] = relationship(
        "ModuleControl", back_populates="module", cascade="all, delete-orphan"
    )


# Add back reference for frameworks.modules after Module definition
ComplianceFramework.modules = relationship("Module", back_populates="framework", cascade="all, delete")  # type: ignore[attr-defined]


class TrainingContent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Content versions for a training module."""

    __tablename__ = "training_content"

    module_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, name="content_type", metadata=Base.metadata, native_enum=False), nullable=False
    )
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    module: Mapped["Module"] = relationship("Module", back_populates="contents")

    __table_args__ = (UniqueConstraint("module_id", "version", name="uq_content_module_version"),)


class ModuleControl(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Associates modules to the controls they satisfy."""

    __tablename__ = "module_controls"

    module_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    control_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)

    module: Mapped["Module"] = relationship("Module", back_populates="controls")
    control: Mapped["Control"] = relationship("Control", back_populates="modules")

    __table_args__ = (UniqueConstraint("module_id", "control_id", name="uq_module_controls_unique"),)


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    """Role assigned to users inside a tenant."""

    __tablename__ = "roles"

    key: Mapped[RoleKey] = mapped_column(
        Enum(RoleKey, name="role_key", metadata=Base.metadata, native_enum=False), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="roles")
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_roles_tenant_key"),
        Index("ix_roles_tenant_id", "tenant_id"),
    )


class User(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    TenantScopedMixin,
):
    """Tenant user (employee/admin)."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", metadata=Base.metadata, native_enum=False),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    manager_user_id: Mapped[uuid.UUID | None] = mapped_column(
        pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    manager: Mapped["User | None"] = relationship("User", remote_side="User.id", back_populates="reports")
    reports: Mapped[list["User"]] = relationship("User", back_populates="manager")
    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment", back_populates="user", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(
        "Assessment", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="actor")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        Index("ix_users_tenant_id", "tenant_id"),
        Index("ix_users_status", "status"),
    )


class UserRole(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    """Join table between users and roles."""

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    tenant: Mapped["Tenant"] = relationship("Tenant")

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "role_id", name="uq_user_roles_unique"),
        Index("ix_user_roles_tenant_id", "tenant_id"),
    )


class Assignment(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, TenantScopedMixin):
    """Assignments of modules to employees."""

    __tablename__ = "assignments"

    user_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    module_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, name="assignment_status", metadata=Base.metadata, native_enum=False),
        nullable=False,
        default=AssignmentStatus.ASSIGNED,
        server_default=AssignmentStatus.ASSIGNED.value,
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    retrain_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="assignments")
    module: Mapped["Module"] = relationship("Module")
    assigned_by: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_by_user_id])

    __table_args__ = (
        Index("ix_assignments_tenant_id", "tenant_id"),
        Index("ix_assignments_status", "status"),
        Index("ix_assignments_due_date", "due_date"),
    )


class Policy(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, TenantScopedMixin):
    """Policies managed for employees to acknowledge."""

    __tablename__ = "policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus, name="policy_status", metadata=Base.metadata, native_enum=False),
        nullable=False,
        default=PolicyStatus.DRAFT,
        server_default=PolicyStatus.DRAFT.value,
    )
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant")
    acknowledgements: Mapped[list["PolicyAcknowledgement"]] = relationship(
        "PolicyAcknowledgement", back_populates="policy", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "version", name="uq_policies_tenant_name_version"),
        Index("ix_policies_tenant_id", "tenant_id"),
    )


class PolicyAcknowledgement(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    """Track which users acknowledged a policy."""

    __tablename__ = "policy_acknowledgements"

    policy_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tenant: Mapped["Tenant"] = relationship("Tenant")
    policy: Mapped["Policy"] = relationship("Policy", back_populates="acknowledgements")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("tenant_id", "policy_id", "user_id", name="uq_policy_ack_unique"),
        Index("ix_policy_acknowledgements_tenant_id", "tenant_id"),
    )


class Event(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    """Events emitted during training activity."""

    __tablename__ = "events"

    user_id: Mapped[uuid.UUID | None] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type", metadata=Base.metadata, native_enum=False), nullable=False
    )
    payload: Mapped[dict | None] = mapped_column(pg.JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tenant: Mapped["Tenant"] = relationship("Tenant")
    user: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        Index("ix_events_tenant_id", "tenant_id"),
        Index("ix_events_occurred_at", "occurred_at"),
    )


class Assessment(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    """Quiz or assessment attempts."""

    __tablename__ = "assessments"

    user_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    module_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        pg.UUID(as_uuid=True), ForeignKey("assignments.id"), nullable=True
    )
    attempt_no: Mapped[int] = mapped_column(nullable=False, server_default="1")
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    answers: Mapped[dict | None] = mapped_column(pg.JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant")
    user: Mapped["User"] = relationship("User", back_populates="assessments")
    module: Mapped["Module"] = relationship("Module")
    assignment: Mapped["Assignment | None"] = relationship("Assignment")

    __table_args__ = (Index("ix_assessments_tenant_id", "tenant_id"),)


class Export(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin):
    """Represents ad-hoc exports triggered by admins."""

    __tablename__ = "exports"

    type: Mapped[ExportType] = mapped_column(
        Enum(ExportType, name="export_type", metadata=Base.metadata, native_enum=False), nullable=False
    )
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus, name="export_status", metadata=Base.metadata, native_enum=False),
        nullable=False,
        default=ExportStatus.PENDING,
        server_default=ExportStatus.PENDING.value,
    )
    storage_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant")
    requested_by: Mapped["User | None"] = relationship("User")

    __table_args__ = (Index("ix_exports_tenant_id", "tenant_id"),)


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Immutable audit log entries per tenant."""

    __tablename__ = "audit_logs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    meta: Mapped[dict | None] = mapped_column(pg.JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="audit_logs")
    actor: Mapped["User | None"] = relationship("User", back_populates="audit_logs")

    __table_args__ = (Index("ix_audit_logs_tenant_id", "tenant_id"),)


__all__ = [
    "Tenant",
    "ComplianceFramework",
    "Control",
    "Module",
    "TrainingContent",
    "ModuleControl",
    "Role",
    "User",
    "UserRole",
    "Assignment",
    "Policy",
    "PolicyAcknowledgement",
    "Event",
    "Assessment",
    "Export",
    "AuditLog",
    "RoleKey",
    "UserStatus",
    "AssignmentStatus",
]
