from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InventoryBalance:
    product_id: str
    bin_id: str
    qty: int
    low_stock_threshold: int | None = None


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
class InventoryMovement:
    movement_id: str
    request_id: str
    product_id: str
    from_bin_id: str
    to_bin_id: str
    qty: int
    moved_by_user_id: str
    reason: str | None = None


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
