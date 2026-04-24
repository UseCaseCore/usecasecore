# Getting Started

This page is kept for compatibility. The canonical quickstart is
`docs/quickstart.md`.

## Install

```bash
pip install usecasecore==0.1.0a2
```

## First mental model

A use case is the explicit runtime boundary for one business action.

Examples:

- `MoveInventory`
- `ReserveInventory`
- `CreateOrder`
- `CancelOrder`

Each use case should:

1. Validate command
2. Check idempotency
3. Load current state
4. Check policy
5. Check transitions
6. Open transaction
7. Apply changes
8. Write audit
9. Emit events
10. Queue side effects
11. Return typed result

## First use case to build

Start with `MoveInventory`.

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
```
