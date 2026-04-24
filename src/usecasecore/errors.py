from __future__ import annotations


class UseCaseError(Exception):
    """Base exception for use-case execution failures."""


class ValidationFailed(UseCaseError):
    """Raised when a command is structurally invalid for the action."""


class PolicyDenied(UseCaseError):
    """Raised when policy rejects the command for the current actor."""


class TransitionDenied(UseCaseError):
    """Raised when the current state cannot move through the requested action."""


class IdempotencyError(UseCaseError):
    """Base exception for idempotency handling failures."""


class IdempotencyConflict(IdempotencyError):
    """Raised when one idempotency key is reused for incompatible work."""


class IdempotencyReplay(IdempotencyError):
    """Raised by stores that choose to short-circuit with a cached result."""

    def __init__(self, result: object) -> None:
        self.result = result
        super().__init__("idempotent result already exists")


class TransactionError(UseCaseError):
    """Raised when an authoritative write boundary fails."""


class RepositoryError(UseCaseError):
    """Raised when a persistence boundary fails."""


class AuditError(UseCaseError):
    """Raised when audit recording fails."""


class EventPublishError(UseCaseError):
    """Raised when domain event publication fails."""


class JobEnqueueError(UseCaseError):
    """Raised when follow-up job enqueueing fails."""
