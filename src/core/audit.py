"""Structured audit events (M055).

Log events, not a table (locked human decision): every security-relevant
action becomes one JSON line on the ``agrin.audit`` logger, which the
M005 ``JsonFormatter`` renders like every other record — ``extra``
fields merge into the object, and JSON encoding defuses log injection.

Event names are stable strings (``auth.login.success`` …) so a log
pipeline can alert on them; ``outcome`` distinguishes success/failure
without parsing messages.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("agrin.audit")


def audit(
    event: str,
    *,
    outcome: str = "success",
    user_id: str | None = None,
    email: str | None = None,
    ip: str | None = None,
    **fields: Any,
) -> None:
    """Emit one audit record. Never raises (logging must not break auth)."""
    payload: dict[str, Any] = {"event": event, "outcome": outcome}
    if user_id is not None:
        payload["user_id"] = user_id
    if email is not None:
        payload["email"] = email
    if ip is not None:
        payload["ip"] = ip
    payload.update(fields)
    logger.info(event, extra=payload)
