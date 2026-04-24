"""UseCaseCore public API."""

from .audit import AuditEntry, AuditSink, InMemoryAuditSink
from .command import Command
from .context import ExecutionContext
from .errors import (
    AuditError,
    EventPublishError,
    IdempotencyConflict,
    IdempotencyError,
    IdempotencyReplay,
    JobEnqueueError,
    PolicyDenied,
    RepositoryError,
    TransactionError,
    TransitionDenied,
    UseCaseError,
    ValidationFailed,
)
from .events import EventBus, InMemoryEventBus
from .idempotency import IdempotencyStore, InMemoryIdempotencyStore
from .jobs import InMemoryJobQueue, JobQueue
from .result import Result
from .transaction import NoopTransactionManager, TransactionManager
from .usecase import UseCase

__all__ = [
    "AuditEntry",
    "AuditError",
    "AuditSink",
    "Command",
    "EventBus",
    "EventPublishError",
    "ExecutionContext",
    "IdempotencyConflict",
    "IdempotencyError",
    "IdempotencyReplay",
    "IdempotencyStore",
    "InMemoryAuditSink",
    "InMemoryEventBus",
    "InMemoryIdempotencyStore",
    "InMemoryJobQueue",
    "JobEnqueueError",
    "JobQueue",
    "NoopTransactionManager",
    "PolicyDenied",
    "RepositoryError",
    "Result",
    "TransactionManager",
    "TransactionError",
    "TransitionDenied",
    "UseCase",
    "UseCaseError",
    "ValidationFailed",
]
