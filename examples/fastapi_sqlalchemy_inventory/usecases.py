from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from usecasecore import (
    EventBus,
    IdempotencyStore,
    JobQueue,
    PolicyDenied,
    TransactionManager,
    TransitionDenied,
    UseCase,
    ValidationFailed,
)
from usecasecore.audit import AuditEntry, AuditSink

from .models import InventoryBalance, InventoryMovement


@dataclass(frozen=True, slots=True)
class MoveInventoryCommand:
    request_id: str
    idempotency_key: str
    product_id: str
    from_bin_id: str
    to_bin_id: str
    qty: int
    moved_by_user_id: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class MoveInventoryResult:
    success: bool
    movement_id: str
    product_id: str
    from_bin_id: str
    to_bin_id: str
    quantity_moved: int
    source_qty_after: int
    dest_qty_after: int


@dataclass(frozen=True, slots=True)
class InventoryMoved:
    movement_id: str
    request_id: str
    product_id: str
    from_bin_id: str
    to_bin_id: str
    qty: int
    moved_by_user_id: str


@dataclass(frozen=True, slots=True)
class LowStockAlert:
    product_id: str
    bin_id: str
    remaining_qty: int
    threshold: int


@dataclass(frozen=True, slots=True)
class MoveInventoryState:
    source: InventoryBalance | None
    destination: InventoryBalance | None


class InventoryRepository(Protocol):
    def get_balance_for_update(
        self,
        product_id: str,
        bin_id: str,
    ) -> InventoryBalance | None:
        """Load the balance this write depends on."""

    def move(
        self,
        command: MoveInventoryCommand,
        source: InventoryBalance,
        destination: InventoryBalance,
    ) -> tuple[InventoryMovement, InventoryBalance, InventoryBalance]:
        """Apply balance changes and create movement history."""


class MoveInventoryUseCase(
    UseCase[MoveInventoryCommand, MoveInventoryState, MoveInventoryResult]
):
    def __init__(
        self,
        *,
        repository: InventoryRepository,
        idempotency_store: IdempotencyStore | None = None,
        audit_sink: AuditSink | None = None,
        event_bus: EventBus | None = None,
        job_queue: JobQueue | None = None,
        transaction_manager: TransactionManager | None = None,
    ) -> None:
        super().__init__(
            idempotency_store=idempotency_store,
            audit_sink=audit_sink,
            event_bus=event_bus,
            job_queue=job_queue,
            transaction_manager=transaction_manager,
        )
        self.repository = repository

    def validate(self, command: MoveInventoryCommand) -> None:
        if command.qty <= 0:
            raise ValidationFailed("qty must be greater than zero")
        if command.from_bin_id == command.to_bin_id:
            raise ValidationFailed("source and destination bins must differ")

    def load_state(self, command: MoveInventoryCommand) -> MoveInventoryState:
        return MoveInventoryState(
            source=self.repository.get_balance_for_update(
                command.product_id,
                command.from_bin_id,
            ),
            destination=self.repository.get_balance_for_update(
                command.product_id,
                command.to_bin_id,
            ),
        )

    def check_policies(
        self,
        command: MoveInventoryCommand,
        state: MoveInventoryState | None,
    ) -> None:
        if not command.moved_by_user_id:
            raise PolicyDenied("moved_by_user_id is required to move inventory")

    def check_transitions(
        self,
        command: MoveInventoryCommand,
        state: MoveInventoryState | None,
    ) -> None:
        if state is None:
            raise TransitionDenied("inventory state was not loaded")
        if state.source is None:
            raise TransitionDenied("source balance does not exist")
        if state.destination is None:
            raise TransitionDenied("destination balance does not exist")
        if state.source.qty < command.qty:
            raise TransitionDenied("source bin does not have enough inventory")
        if state.source.qty - command.qty < 0:
            raise TransitionDenied("move would create negative inventory")

    def apply(
        self,
        command: MoveInventoryCommand,
        state: MoveInventoryState | None,
    ) -> MoveInventoryResult:
        if state is None or state.source is None or state.destination is None:
            raise TransitionDenied("inventory state was not loaded")

        movement, source, destination = self.repository.move(
            command,
            source=state.source,
            destination=state.destination,
        )
        return MoveInventoryResult(
            success=True,
            movement_id=movement.movement_id,
            product_id=command.product_id,
            from_bin_id=command.from_bin_id,
            to_bin_id=command.to_bin_id,
            quantity_moved=command.qty,
            source_qty_after=source.qty,
            dest_qty_after=destination.qty,
        )

    def write_audit(
        self,
        command: MoveInventoryCommand,
        state: MoveInventoryState | None,
        result: MoveInventoryResult,
    ) -> None:
        if self.audit_sink is None:
            return None

        self.audit_sink.write(
            AuditEntry(
                action="MoveInventory",
                actor_id=command.moved_by_user_id,
                payload={
                    "request_id": command.request_id,
                    "movement_id": result.movement_id,
                    "product_id": command.product_id,
                    "from_bin_id": command.from_bin_id,
                    "to_bin_id": command.to_bin_id,
                    "qty": command.qty,
                    "reason": command.reason,
                },
            )
        )

    def emit_events(
        self,
        command: MoveInventoryCommand,
        state: MoveInventoryState | None,
        result: MoveInventoryResult,
    ) -> None:
        if self.event_bus is None:
            return None

        self.event_bus.publish(
            InventoryMoved(
                movement_id=result.movement_id,
                request_id=command.request_id,
                product_id=command.product_id,
                from_bin_id=command.from_bin_id,
                to_bin_id=command.to_bin_id,
                qty=command.qty,
                moved_by_user_id=command.moved_by_user_id,
            )
        )

    def enqueue_jobs(
        self,
        command: MoveInventoryCommand,
        state: MoveInventoryState | None,
        result: MoveInventoryResult,
    ) -> None:
        if self.job_queue is None or state is None or state.source is None:
            return None

        threshold = state.source.low_stock_threshold
        if threshold is None:
            return None

        if result.source_qty_after <= threshold:
            self.job_queue.enqueue(
                LowStockAlert(
                    product_id=command.product_id,
                    bin_id=command.from_bin_id,
                    remaining_qty=result.source_qty_after,
                    threshold=threshold,
                )
            )
