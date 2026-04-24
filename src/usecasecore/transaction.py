from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from typing import Any, Protocol


class TransactionManager(Protocol):
    """Creates a transaction context for authoritative changes."""

    def __call__(self) -> AbstractContextManager[Any]:
        """Return a context manager that commits or rolls back work."""


class NoopTransactionManager:
    """Default transaction manager for examples and pure unit tests."""

    def __call__(self) -> AbstractContextManager[Any]:
        return nullcontext()
