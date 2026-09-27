"""ORM models package.

Importing this package registers every model on ``Base.metadata`` — Alembic's
``env.py`` relies on that for ``--autogenerate`` (M004/M008).
"""

from __future__ import annotations

from src.models.base import Base
from src.models.user import User, UserRole

__all__ = ["Base", "User", "UserRole"]
