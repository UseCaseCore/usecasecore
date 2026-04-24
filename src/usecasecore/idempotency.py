from __future__ import annotations

from typing import Protocol

from .errors import IdempotencyConflict


class IdempotencyStore(Protocol):
    """Stores completed results by idempotency key."""

    def get(self, key: str) -> object | None:
        """Return the stored result, if any."""

    def save(self, key: str, result: object) -> None:
        """Persist the result for a completed key."""


class InMemoryIdempotencyStore:
    """Small idempotency store for examples and tests."""

    def __init__(self) -> None:
        self._results: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._results.get(key)

    def save(self, key: str, result: object) -> None:
        existing = self._results.get(key)
        if existing is not None and existing != result:
            raise IdempotencyConflict(f"idempotency key already used: {key}")
        self._results[key] = result
