# Quickstart

## Install

```bash
pip install usecasecore==0.1.0a2
```

## First mental model

A use case is the explicit runtime boundary for one business action.

```text
Command -> validate -> idempotency -> state -> policy -> transaction -> result
```

Start with one real action. For UseCaseCore, the canonical example is
`MoveInventory`.

```python
from examples.move_inventory import (
    InMemoryInventoryRepository,
    MoveInventoryCommand,
    MoveInventoryUseCase,
)
from usecasecore import InMemoryIdempotencyStore

repository = InMemoryInventoryRepository()
repository.set_balance("sku-1", "A", 10)
repository.set_balance("sku-1", "B", 1)

use_case = MoveInventoryUseCase(
    repository=repository,
    idempotency_store=InMemoryIdempotencyStore(),
)

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

assert result.success is True
assert result.source_qty_after == 6
assert result.dest_qty_after == 5
```
