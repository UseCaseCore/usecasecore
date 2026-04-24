from __future__ import annotations

from typing import Protocol


class JobQueueAdapter(Protocol):
    """Queues explicit side effects after the use case commits truth."""

    def enqueue(self, job: object) -> None:
        """Enqueue one job."""
