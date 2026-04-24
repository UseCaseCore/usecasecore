from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from .models import InventoryBalance, InventoryMovement, MoveInventoryCommand


class InventoryRepository(Protocol):
    def get_balance_for_update(
        self,
        product_id: str,
        bin_id: str,
    ) -> InventoryBalance | None:
        """Load the balance this write depends on, with locking in real stores."""

    def save_balance(self, balance: InventoryBalance) -> None:
        """Persist one updated balance."""

    def create_movement(
        self,
        command: MoveInventoryCommand,
        source_after: InventoryBalance,
        destination_after: InventoryBalance,
    ) -> InventoryMovement:
        """Persist movement history for the inventory change."""

    def move(
        self,
        command: MoveInventoryCommand,
        source: InventoryBalance,
        destination: InventoryBalance,
    ) -> tuple[InventoryMovement, InventoryBalance, InventoryBalance]:
        """Apply the balance updates and movement history."""


class InMemoryInventoryRepository:
    def __init__(self) -> None:
        self._balances: dict[tuple[str, str], InventoryBalance] = {}
        self.movements: list[InventoryMovement] = []

    def set_balance(
        self,
        product_id: str,
        bin_id: str,
        qty: int,
        *,
        low_stock_threshold: int | None = None,
    ) -> None:
        self._balances[(product_id, bin_id)] = InventoryBalance(
            product_id=product_id,
            bin_id=bin_id,
            qty=qty,
            low_stock_threshold=low_stock_threshold,
        )

    def get_balance_for_update(
        self,
        product_id: str,
        bin_id: str,
    ) -> InventoryBalance | None:
        return self._balances.get((product_id, bin_id))

    def save_balance(self, balance: InventoryBalance) -> None:
        self._balances[(balance.product_id, balance.bin_id)] = balance

    def create_movement(
        self,
        command: MoveInventoryCommand,
        source_after: InventoryBalance,
        destination_after: InventoryBalance,
    ) -> InventoryMovement:
        movement = InventoryMovement(
            movement_id=f"movement-{len(self.movements) + 1}",
            request_id=command.request_id,
            product_id=command.product_id,
            from_bin_id=command.from_bin_id,
            to_bin_id=command.to_bin_id,
            qty=command.qty,
            moved_by_user_id=command.moved_by_user_id,
            reason=command.reason,
        )
        self.movements.append(movement)
        return movement

    def move(
        self,
        command: MoveInventoryCommand,
        source: InventoryBalance,
        destination: InventoryBalance,
    ) -> tuple[InventoryMovement, InventoryBalance, InventoryBalance]:
        source_after = replace(source, qty=source.qty - command.qty)
        destination_after = replace(destination, qty=destination.qty + command.qty)
        self.save_balance(source_after)
        self.save_balance(destination_after)
        movement = self.create_movement(
            command,
            source_after=source_after,
            destination_after=destination_after,
        )
        return movement, source_after, destination_after
