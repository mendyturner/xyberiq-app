"""User domain service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password, verify_password
from app.db.models import Role, RoleKey, User, UserRole


class UserService:
    """Encapsulates user operations."""

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    @classmethod
    def create_user(
        cls,
        *,
        db: Session,
        tenant_id: uuid.UUID,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        roles: list[RoleKey] | None = None,
    ) -> User:
        normalized_email = cls._normalize_email(email)
        user = User(
            tenant_id=tenant_id,
            email=normalized_email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
        )
        db.add(user)
        db.flush()

        if roles:
            cls.assign_roles(db=db, tenant_id=tenant_id, user=user, roles=roles)

        return user

    @staticmethod
    def assign_roles(
        *,
        db: Session,
        tenant_id: uuid.UUID,
        user: User,
        roles: list[RoleKey],
    ) -> None:
        for role_key in roles:
            role_stmt = (
                select(Role)
                .where(Role.tenant_id == tenant_id, Role.key == role_key)
                .execution_options(tenant_aware=False)
            )
            role = db.execute(role_stmt).scalar_one_or_none()
            if role is None:
                raise ValueError(f"Role {role_key} not provisioned for tenant {tenant_id}")

            existing = (
                select(UserRole)
                .where(
                    UserRole.tenant_id == tenant_id,
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id,
                )
                .execution_options(tenant_aware=False)
            )
            if db.execute(existing).scalar_one_or_none() is None:
                db.add(UserRole(tenant_id=tenant_id, user_id=user.id, role_id=role.id))

    @classmethod
    def authenticate(cls, *, db: Session, tenant_id: uuid.UUID, email: str, password: str) -> User | None:
        normalized_email = cls._normalize_email(email)
        stmt = (
            select(User)
            .options(joinedload(User.roles).joinedload(UserRole.role))
            .where(User.tenant_id == tenant_id, User.email == normalized_email)
        )
        user = db.execute(stmt).scalars().first()
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @classmethod
    def get_by_email(cls, *, db: Session, tenant_id: uuid.UUID, email: str) -> User | None:
        stmt = (
            select(User)
            .options(joinedload(User.roles).joinedload(UserRole.role))
            .where(User.tenant_id == tenant_id, User.email == cls._normalize_email(email))
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_by_id(*, db: Session, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id).options(joinedload(User.roles).joinedload(UserRole.role))
        return db.execute(stmt).scalars().first()

    @staticmethod
    def set_password(*, db: Session, user: User, password: str) -> None:
        user.password_hash = hash_password(password)
        db.add(user)


__all__ = ["UserService"]
