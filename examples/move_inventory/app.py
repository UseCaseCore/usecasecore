from __future__ import annotations

from examples.move_inventory.repositories import InMemoryInventoryRepository
from examples.move_inventory.usecases import MoveInventoryCommand, MoveInventoryUseCase


def main() -> None:
    repository = InMemoryInventoryRepository()
    repository.set_balance(
        product_id="sku-1",
        bin_id="A",
        qty=10,
        low_stock_threshold=6,
    )
    repository.set_balance(product_id="sku-1", bin_id="B", qty=1)

    use_case = MoveInventoryUseCase(repository=repository)
    result = use_case.execute(
        MoveInventoryCommand(
            request_id="req-1",
            idempotency_key="move-sku-1-A-B-4",
            product_id="sku-1",
            from_bin_id="A",
            to_bin_id="B",
            qty=4,
            moved_by_user_id="user-1",
            reason="rebalancing",
        )
    )

    print(result)


if __name__ == "__main__":
    main()
