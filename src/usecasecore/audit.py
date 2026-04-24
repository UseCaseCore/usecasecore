from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """Structured trace for a state-changing action."""

    action: str
    actor_id: str | None = None
    payload: Mapping[str, object] = field(default_factory=dict)


class AuditSink(Protocol):
    """Stores audit entries produced by use cases."""

    def write(self, entry: AuditEntry) -> None:
        """Persist one audit entry."""


class InMemoryAuditSink:
    """Small audit sink for examples and tests."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def write(self, entry: AuditEntry) -> None:
        self.entries.append(entry)
