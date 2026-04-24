from __future__ import annotations

from typing import Protocol


class EventBus(Protocol):
    """Publishes domain events from completed use cases."""

    def publish(self, event: object) -> None:
        """Publish one event."""


class InMemoryEventBus:
    """Small event bus for examples and tests."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def publish(self, event: object) -> None:
        self.events.append(event)
