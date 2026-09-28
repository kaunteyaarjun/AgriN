"""Provider registry: explicit registration, settings-driven resolution (M021).

One instance is cached per ``(family, mode)`` key; registration is an
explicit decorator (no import-time auto-discovery — grep-able and
mypy-friendly). ``ProviderRegistry`` is instantiable so tests can use
fresh, isolated registries; ``default_registry`` is the process-wide one
that ``register`` / ``get_provider`` operate on.

Mode resolution: ``get_provider("weather")`` with no explicit mode reads
``get_settings().weather_provider`` (``demo``/``live``, M002). Settings
are read at *get* time, never at registration time.
"""

from __future__ import annotations

from src.core.config import ProviderMode, get_settings
from src.providers.base import KNOWN_FAMILIES, BaseProvider
from src.providers.errors import ProviderError, ProviderNotRegistered

_VALID_MODES: tuple[ProviderMode, ...] = ("demo", "live")


class ProviderRegistry:
    """Maps ``(family, mode)`` to a provider class and its cached instance."""

    def __init__(self) -> None:
        self._classes: dict[tuple[str, str], type[BaseProvider]] = {}
        self._instances: dict[tuple[str, str], BaseProvider] = {}

    def register(self, provider_cls: type[BaseProvider]) -> type[BaseProvider]:
        """Class decorator: validate metadata and claim the ``(family, mode)`` key."""
        family = getattr(provider_cls, "family", None)
        mode = getattr(provider_cls, "mode", None)
        name = getattr(provider_cls, "name", None)
        if not isinstance(family, str) or family not in KNOWN_FAMILIES:
            raise ProviderError(
                f"provider family must be one of: {', '.join(KNOWN_FAMILIES)} (got {family!r})"
            )
        if mode not in _VALID_MODES:
            raise ProviderError(
                f"provider mode must be one of: {', '.join(_VALID_MODES)} (got {mode!r})"
            )
        if not isinstance(name, str) or not name.strip():
            raise ProviderError("provider name must be a non-empty string")
        key = (family, mode)
        if key in self._classes:
            existing = self._classes[key]
            raise ProviderError(
                f"({family!r}, {mode!r}) is already registered by {existing.__qualname__}"
            )
        self._classes[key] = provider_cls
        return provider_cls

    def get(self, family: str, mode: ProviderMode) -> BaseProvider:
        """Return the cached instance for ``(family, mode)``, constructing it once."""
        key = (family, mode)
        if key not in self._classes:
            registered = sorted(f"{f}/{m}" for f, m in self._classes if f == family)
            known = ", ".join(KNOWN_FAMILIES)
            raise ProviderNotRegistered(
                f"No provider registered for family={family!r} mode={mode!r}. "
                f"Registered for this family: {', '.join(registered) or 'none'}. "
                f"Known families: {known}."
            )
        instance = self._instances.get(key)
        if instance is None:
            instance = self._classes[key]()
            self._instances[key] = instance
        return instance

    async def aclose_all(self) -> None:
        """Await every cached instance's ``aclose``; next ``get`` re-constructs."""
        for instance in list(self._instances.values()):
            await instance.aclose()
        self._instances.clear()


default_registry = ProviderRegistry()
"""Process-wide registry; concrete providers decorate onto this."""


def register(provider_cls: type[BaseProvider]) -> type[BaseProvider]:
    """Register a provider class on ``default_registry`` (decorator)."""
    return default_registry.register(provider_cls)


def get_provider(family: str, *, mode: ProviderMode | None = None) -> BaseProvider:
    """Resolve a provider by family; ``mode`` defaults to the settings flag."""
    if mode is None:
        settings_mode = getattr(get_settings(), f"{family}_provider", None)
        if settings_mode is None:
            known = ", ".join(KNOWN_FAMILIES)
            raise ProviderNotRegistered(
                f"Unknown provider family {family!r}. Known families: {known}."
            )
        mode = settings_mode
    return default_registry.get(family, mode)
