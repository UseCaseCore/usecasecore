from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Generic, cast

from .audit import AuditEntry, AuditSink
from .context import ExecutionContext
from .events import EventBus
from .idempotency import IdempotencyStore
from .jobs import JobQueue
from .result import Result
from .transaction import NoopTransactionManager, TransactionManager
from .types import CommandT, ResultT, StateT


class UseCase(Generic[CommandT, StateT, ResultT]):
    """Base class for one explicit business action."""

    def __init__(
        self,
        *,
        context: ExecutionContext | None = None,
        idempotency_store: IdempotencyStore | None = None,
        audit_sink: AuditSink | None = None,
        event_bus: EventBus | None = None,
        job_queue: JobQueue | None = None,
        transaction_manager: TransactionManager
        | Callable[[], AbstractContextManager[Any]]
        | None = None,
    ) -> None:
        self.context = context or ExecutionContext()
        self.idempotency_store = idempotency_store
        self.audit_sink = audit_sink
        self.event_bus = event_bus
        self.job_queue = job_queue
        self._transaction_manager = transaction_manager or NoopTransactionManager()

    def validate(self, command: CommandT) -> None:
        return None

    def idempotency_key(self, command: CommandT) -> str | None:
        command_key = getattr(command, "idempotency_key", None)
        return command_key or self.context.idempotency_key

    def check_idempotency(self, command: CommandT) -> ResultT | None:
        if self.idempotency_store is None:
            return None

        key = self.idempotency_key(command)
        if key is None:
            return None

        result = self.idempotency_store.get(key)
        if result is None:
            return None

        return cast(ResultT, result)

    def load_state(self, command: CommandT) -> StateT | None:
        return None

    def check_policies(self, command: CommandT, state: StateT | None) -> None:
        return None

    def check_transitions(self, command: CommandT, state: StateT | None) -> None:
        return None

    def transaction(self) -> AbstractContextManager[Any]:
        return self._transaction_manager()

    def apply(self, command: CommandT, state: StateT | None) -> ResultT:
        raise NotImplementedError

    def write_audit(
        self,
        command: CommandT,
        state: StateT | None,
        result: ResultT,
    ) -> None:
        if self.audit_sink is None or not isinstance(result, Result):
            return None
        if result.audit is None:
            return None

        self.audit_sink.write(
            AuditEntry(
                action=self.audit_action(command),
                actor_id=self.actor_id(command),
                payload=result.audit,
            )
        )
        return None

    def emit_events(
        self,
        command: CommandT,
        state: StateT | None,
        result: ResultT,
    ) -> None:
        if self.event_bus is None or not isinstance(result, Result):
            return None

        for event in result.events:
            self.event_bus.publish(event)

        return None

    def enqueue_jobs(
        self,
        command: CommandT,
        state: StateT | None,
        result: ResultT,
    ) -> None:
        if self.job_queue is None or not isinstance(result, Result):
            return None

        for job in result.jobs:
            self.job_queue.enqueue(job)

        return None

    def remember_idempotency(self, command: CommandT, result: ResultT) -> None:
        if self.idempotency_store is None:
            return None

        key = self.idempotency_key(command)
        if key is None:
            return None

        self.idempotency_store.save(key, result)
        return None

    def actor_id(self, command: CommandT) -> str | None:
        command_actor_id = getattr(command, "actor_id", None)
        return command_actor_id or self.context.actor_id

    def audit_action(self, command: CommandT) -> str:
        name = self.__class__.__name__
        return name.removesuffix("UseCase")

    def execute(self, command: CommandT) -> ResultT:
        self.validate(command)
        replayed = self.check_idempotency(command)
        if replayed is not None:
            return replayed

        state = self.load_state(command)
        self.check_policies(command, state)
        self.check_transitions(command, state)

        with self.transaction():
            result = self.apply(command, state)
            self.write_audit(command, state, result)
            self.emit_events(command, state, result)
            self.enqueue_jobs(command, state, result)
            self.remember_idempotency(command, result)

        return result
