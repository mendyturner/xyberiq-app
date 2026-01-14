"""Domain enumerations shared across models and schemas."""

from __future__ import annotations

from enum import Enum


class RoleKey(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR = "hr"
    IT = "it"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ControlType(str, Enum):
    ADMINISTRATIVE = "administrative"
    TECHNICAL = "technical"
    PHYSICAL = "physical"


class ContentType(str, Enum):
    VIDEO = "video"
    SCORM = "scorm"
    PDF = "pdf"
    QUIZ = "quiz"
    SIMULATION = "simulation"


class AssignmentStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class EventType(str, Enum):
    PHISH_FAIL = "phish_fail"
    POLICY_ACK = "policy_ack"
    LOGIN = "login"
    QUIZ_ATTEMPT = "quiz_attempt"
    CONTENT_VIEW = "content_view"


class ExportType(str, Enum):
    EMPLOYEES_CSV = "employees_csv"
    ASSIGNMENTS_CSV = "assignments_csv"
    EVIDENCE_ZIP = "evidence_zip"


class ExportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


__all__ = [
    "RoleKey",
    "UserStatus",
    "ControlType",
    "ContentType",
    "AssignmentStatus",
    "EventType",
    "ExportType",
    "ExportStatus",
    "PolicyStatus",
]
