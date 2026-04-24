# MoveInventory

A request like `MoveInventory` looks simple at the UI layer. In practice, it
needs validation, current-state reads, permission checks, transaction
boundaries, audit, and safe side effects.

```text
MoveInventoryCommand
  -> Load source + destination balances
  -> Check permission + invariants
  -> Open transaction
  -> Create movement history
  -> Write audit + emit InventoryMoved
  -> Queue LowStockAlert
  -> MoveInventoryResult
```

UseCaseCore makes this path explicit and reusable instead of re-implementing it
in every service.

## Runtime pieces

The example uses:

- `MoveInventoryCommand` as typed input
- `MoveInventoryState` for loaded source and destination balances
- `MoveInventoryResult` as the stable return value
- `InMemoryInventoryRepository` as the persistence boundary
- `get_balance_for_update()` to show the read-before-write dependency
- movement history creation through the repository
- `AuditSink`, `EventBus`, and `JobQueue` hooks for explicit side effects
- `IdempotencyStore` replay so a retried command does not duplicate writes
