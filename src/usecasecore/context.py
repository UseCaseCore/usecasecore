from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Request and actor metadata available to every use case hook."""

    request_id: str | None = None
    actor_id: str | None = None
    correlation_id: str | None = None
    tenant_id: str | None = None
    idempotency_key: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Mapping[str, object] = field(default_factory=dict)
