from __future__ import annotations

import unittest

from examples.move_inventory import (
    InMemoryInventoryRepository,
    InventoryMoved,
    LowStockAlert,
    MoveInventoryCommand,
    MoveInventoryUseCase,
)
from usecasecore import (
    InMemoryAuditSink,
    InMemoryEventBus,
    InMemoryIdempotencyStore,
    InMemoryJobQueue,
    TransitionDenied,
    ValidationFailed,
)


class MoveInventoryTests(unittest.TestCase):
    def test_updates_balances_and_records_side_effects(self) -> None:
        repository = InMemoryInventoryRepository()
        repository.set_balance("sku-1", "A", 10, low_stock_threshold=6)
        repository.set_balance("sku-1", "B", 1)

        audit_sink = InMemoryAuditSink()
        event_bus = InMemoryEventBus()
        job_queue = InMemoryJobQueue()
        use_case = MoveInventoryUseCase(
            repository=repository,
            audit_sink=audit_sink,
            event_bus=event_bus,
            job_queue=job_queue,
        )

        result = use_case.execute(
            MoveInventoryCommand(
                request_id="req-1",
                idempotency_key="move-1",
                product_id="sku-1",
                from_bin_id="A",
                to_bin_id="B",
                qty=4,
                moved_by_user_id="user-1",
                reason="rebalancing",
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.movement_id, "movement-1")
        self.assertEqual(result.source_qty_after, 6)
        self.assertEqual(result.dest_qty_after, 5)
        self.assertEqual(audit_sink.entries[0].action, "MoveInventory")
        self.assertEqual(audit_sink.entries[0].actor_id, "user-1")
        self.assertEqual(audit_sink.entries[0].payload["movement_id"], "movement-1")
        self.assertEqual(
            event_bus.events,
            [
                InventoryMoved(
                    movement_id="movement-1",
                    request_id="req-1",
                    product_id="sku-1",
                    from_bin_id="A",
                    to_bin_id="B",
                    qty=4,
                    moved_by_user_id="user-1",
                )
            ],
        )
        self.assertEqual(
            job_queue.jobs,
            [
                LowStockAlert(
                    product_id="sku-1",
                    bin_id="A",
                    remaining_qty=6,
                    threshold=6,
                )
            ],
        )

    def test_idempotency_replays_without_duplicate_writes_or_side_effects(self) -> None:
        repository = InMemoryInventoryRepository()
        repository.set_balance("sku-1", "A", 10, low_stock_threshold=10)
        repository.set_balance("sku-1", "B", 1)

        audit_sink = InMemoryAuditSink()
        event_bus = InMemoryEventBus()
        job_queue = InMemoryJobQueue()
        use_case = MoveInventoryUseCase(
            repository=repository,
            idempotency_store=InMemoryIdempotencyStore(),
            audit_sink=audit_sink,
            event_bus=event_bus,
            job_queue=job_queue,
        )
        command = MoveInventoryCommand(
            request_id="req-1",
            idempotency_key="move-1",
            product_id="sku-1",
            from_bin_id="A",
            to_bin_id="B",
            qty=4,
            moved_by_user_id="user-1",
        )

        first = use_case.execute(command)
        second = use_case.execute(command)

        self.assertEqual(first, second)
        source = repository.get_balance_for_update("sku-1", "A")
        destination = repository.get_balance_for_update("sku-1", "B")
        self.assertIsNotNone(source)
        self.assertIsNotNone(destination)
        self.assertEqual(source.qty if source else None, 6)
        self.assertEqual(destination.qty if destination else None, 5)
        self.assertEqual(len(repository.movements), 1)
        self.assertEqual(len(audit_sink.entries), 1)
        self.assertEqual(len(event_bus.events), 1)
        self.assertEqual(len(job_queue.jobs), 1)

    def test_rejects_invalid_quantity(self) -> None:
        repository = InMemoryInventoryRepository()
        use_case = MoveInventoryUseCase(repository=repository)

        with self.assertRaises(ValidationFailed):
            use_case.execute(
                MoveInventoryCommand(
                    request_id="req-1",
                    idempotency_key="move-1",
                    product_id="sku-1",
                    from_bin_id="A",
                    to_bin_id="B",
                    qty=0,
                    moved_by_user_id="user-1",
                )
            )

    def test_requires_available_source_balance(self) -> None:
        repository = InMemoryInventoryRepository()
        repository.set_balance("sku-1", "A", 1)
        repository.set_balance("sku-1", "B", 1)
        use_case = MoveInventoryUseCase(repository=repository)

        with self.assertRaises(TransitionDenied):
            use_case.execute(
                MoveInventoryCommand(
                    request_id="req-1",
                    idempotency_key="move-1",
                    product_id="sku-1",
                    from_bin_id="A",
                    to_bin_id="B",
                    qty=4,
                    moved_by_user_id="user-1",
                )
            )

    def test_requires_existing_destination_balance(self) -> None:
        repository = InMemoryInventoryRepository()
        repository.set_balance("sku-1", "A", 10)
        use_case = MoveInventoryUseCase(repository=repository)

        with self.assertRaises(TransitionDenied):
            use_case.execute(
                MoveInventoryCommand(
                    request_id="req-1",
                    idempotency_key="move-1",
                    product_id="sku-1",
                    from_bin_id="A",
                    to_bin_id="B",
                    qty=4,
                    moved_by_user_id="user-1",
                )
            )
