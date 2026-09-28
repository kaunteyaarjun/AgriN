"""BaseProvider: the metadata contract shared by every provider (M021).

Concrete providers subclass this (plus their family's ABC, e.g.
``WeatherProvider``), set the three ClassVars, and are registered with
the registry (M021 pattern). Instantiation is the registry's job at
``get`` time — one instance per ``(family, mode)`` key.
"""

from __future__ import annotations

from abc import ABC
from typing import ClassVar

from src.core.config import ProviderMode

KNOWN_FAMILIES: tuple[str, ...] = ("weather", "satellite", "soil", "disease", "llm")
"""Exactly the five provider mode flags in ``Settings`` (M002)."""


class BaseProvider(ABC):
    """Metadata + lifecycle for one external-data source implementation."""

    family: ClassVar[str]
    mode: ClassVar[ProviderMode]
    name: ClassVar[str]

    def __repr__(self) -> str:
        return f"<{type(self).__name__} family={self.family} mode={self.mode} name={self.name}>"

    async def aclose(self) -> None:
        """Release per-instance resources (HTTP clients, file handles).

        No-op by default; live providers override. ``registry.aclose_all``
        awaits it on shutdown.
        """
        return None
