from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from usecasecore import (
    ExecutionContext,
    InMemoryAuditSink,
    InMemoryEventBus,
    InMemoryIdempotencyStore,
    InMemoryJobQueue,
    Result,
    UseCase,
)


class RecordingTransaction:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def __enter__(self) -> None:
        self.calls.append("transaction.enter")

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        self.calls.append("transaction.exit")
        return False


class RecordingUseCase(UseCase[str, str, str]):
    def __init__(self) -> None:
        self.calls: list[str] = []
        super().__init__(transaction_manager=lambda: RecordingTransaction(self.calls))

    def validate(self, command: str) -> None:
        self.calls.append("validate")

    def check_idempotency(self, command: str) -> None:
        self.calls.append("check_idempotency")

    def load_state(self, command: str) -> str:
        self.calls.append("load_state")
        return "state"

    def check_policies(self, command: str, state: str | None) -> None:
        self.calls.append("check_policies")

    def check_transitions(self, command: str, state: str | None) -> None:
        self.calls.append("check_transitions")

    def apply(self, command: str, state: str | None) -> str:
        self.calls.append("apply")
        return "result"

    def write_audit(self, command: str, state: str | None, result: str) -> None:
        self.calls.append("write_audit")

    def emit_events(self, command: str, state: str | None, result: str) -> None:
        self.calls.append("emit_events")

    def enqueue_jobs(self, command: str, state: str | None, result: str) -> None:
        self.calls.append("enqueue_jobs")


class ResultMetadataUseCase(UseCase[str, None, Result[str]]):
    def apply(self, command: str, state: None) -> Result[str]:
        return (
            Result.ok("done")
            .with_audit({"command": command})
            .with_event("InventoryMoved")
            .with_job("LowStockAlert")
        )


@dataclass(frozen=True, slots=True)
class IdempotentCommand:
    idempotency_key: str
    value: str


class CountingUseCase(UseCase[IdempotentCommand, None, str]):
    def __init__(self, store: InMemoryIdempotencyStore) -> None:
        super().__init__(idempotency_store=store)
        self.apply_count = 0

    def apply(self, command: IdempotentCommand, state: None) -> str:
        self.apply_count += 1
        return f"{command.value}:{self.apply_count}"


class EventFailureUseCase(CountingUseCase):
    def emit_events(
        self,
        command: IdempotentCommand,
        state: None,
        result: str,
    ) -> None:
        raise RuntimeError("event bus unavailable")


class UseCaseBaseTests(unittest.TestCase):
    def test_execute_runs_hooks_in_order(self) -> None:
        use_case = RecordingUseCase()

        self.assertEqual(use_case.execute("command"), "result")
        self.assertEqual(
            use_case.calls,
            [
                "validate",
                "check_idempotency",
                "load_state",
                "check_policies",
                "check_transitions",
                "transaction.enter",
                "apply",
                "write_audit",
                "emit_events",
                "enqueue_jobs",
                "transaction.exit",
            ],
        )

    def test_base_apply_must_be_implemented(self) -> None:
        use_case: UseCase[Any, Any, Any] = UseCase()

        with self.assertRaises(NotImplementedError):
            use_case.execute(object())

    def test_result_metadata_dispatches_to_configured_infrastructure(self) -> None:
        audit_sink = InMemoryAuditSink()
        event_bus = InMemoryEventBus()
        job_queue = InMemoryJobQueue()
        use_case = ResultMetadataUseCase(
            context=ExecutionContext(actor_id="user-1"),
            audit_sink=audit_sink,
            event_bus=event_bus,
            job_queue=job_queue,
        )

        result = use_case.execute("move")

        self.assertEqual(result.value, "done")
        self.assertEqual(audit_sink.entries[0].action, "ResultMetadata")
        self.assertEqual(audit_sink.entries[0].actor_id, "user-1")
        self.assertEqual(audit_sink.entries[0].payload, {"command": "move"})
        self.assertEqual(event_bus.events, ["InventoryMoved"])
        self.assertEqual(job_queue.jobs, ["LowStockAlert"])

    def test_idempotency_replays_saved_result_without_reapplying(self) -> None:
        store = InMemoryIdempotencyStore()
        use_case = CountingUseCase(store)

        first = use_case.execute(IdempotentCommand("key-1", "first"))
        second = use_case.execute(IdempotentCommand("key-1", "second"))

        self.assertEqual(first, "first:1")
        self.assertEqual(second, "first:1")
        self.assertEqual(use_case.apply_count, 1)

    def test_event_failure_propagates_and_does_not_remember_idempotency(self) -> None:
        store = InMemoryIdempotencyStore()
        use_case = EventFailureUseCase(store)
        command = IdempotentCommand("key-1", "first")

        with self.assertRaises(RuntimeError):
            use_case.execute(command)

        with self.assertRaises(RuntimeError):
            use_case.execute(IdempotentCommand("key-1", "retry"))

        self.assertEqual(use_case.apply_count, 2)
