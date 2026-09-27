"""Shared SQLAlchemy declarative base for all AgriN models.

Future model milestones import ``Base`` from here so that Alembic's
``target_metadata`` sees every table and ``--autogenerate`` works.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""
