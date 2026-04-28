from __future__ import annotations

from pydantic import BaseModel

from .usecases import MoveInventoryCommand, MoveInventoryResult


class MoveInventoryRequest(BaseModel):
    request_id: str
    idempotency_key: str
    product_id: str
    from_bin_id: str
    to_bin_id: str
    qty: int
    moved_by_user_id: str
    reason: str | None = None

    def to_command(self) -> MoveInventoryCommand:
        return MoveInventoryCommand(
            request_id=self.request_id,
            idempotency_key=self.idempotency_key,
            product_id=self.product_id,
            from_bin_id=self.from_bin_id,
            to_bin_id=self.to_bin_id,
            qty=self.qty,
            moved_by_user_id=self.moved_by_user_id,
            reason=self.reason,
        )


class MoveInventoryResponse(BaseModel):
    success: bool
    movement_id: str
    product_id: str
    from_bin_id: str
    to_bin_id: str
    quantity_moved: int
    source_qty_after: int
    dest_qty_after: int

    @classmethod
    def from_result(cls, result: MoveInventoryResult) -> MoveInventoryResponse:
        return cls(
            success=result.success,
            movement_id=result.movement_id,
            product_id=result.product_id,
            from_bin_id=result.from_bin_id,
            to_bin_id=result.to_bin_id,
            quantity_moved=result.quantity_moved,
            source_qty_after=result.source_qty_after,
            dest_qty_after=result.dest_qty_after,
        )
