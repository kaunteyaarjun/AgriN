"""User model: accounts for farmers, extension officers and admins (M008)."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class UserRole(StrEnum):
    """Roles enforced by RBAC from M010 onward (default-deny)."""

    farmer = "farmer"
    extension_officer = "extension_officer"
    admin = "admin"


class User(Base):
    """An AgriN account. Passwords are stored only as bcrypt hashes."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # VARCHAR + CHECK (not a native PG enum): native enum types survive
    # drop_table and break the migration round-trip test (see M008 notes).
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            length=32,
            create_constraint=True,
        ),
        nullable=False,
        default=UserRole.farmer,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:  # never include password_hash
        return f"User(id={self.id!r}, email={self.email!r}, role={self.role!r})"
