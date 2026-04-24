from __future__ import annotations

from typing import Protocol


class JobQueue(Protocol):
    """Queues explicit follow-up work after a use case commits truth."""

    def enqueue(self, job: object) -> None:
        """Enqueue one job."""


class InMemoryJobQueue:
    """Small job queue for examples and tests."""

    def __init__(self) -> None:
        self.jobs: list[object] = []

    def enqueue(self, job: object) -> None:
        self.jobs.append(job)
