from __future__ import annotations

from typing import Protocol


class EventBusAdapter(Protocol):
    """Publishes domain events after the authoritative change is complete."""

    def publish(self, event: object) -> None:
        """Publish one event."""
