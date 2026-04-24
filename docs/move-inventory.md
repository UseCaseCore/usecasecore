# MoveInventory Example

This page is kept for compatibility. The canonical page is
`docs/examples/move-inventory.md`.

## Flow

```text
MoveInventoryCommand
  -> Load source + destination balances
  -> Check permission
  -> Check invariants
  -> Open transaction
  -> Update balances
  -> Create movement history
  -> Write audit
  -> Emit InventoryMoved
  -> Queue LowStockAlert
  -> Commit
  -> MoveInventoryResult
```

## Why it matters

A move looks simple at the UI layer.

In practice it needs:

- validation
- current-state reads
- permission checks
- transaction boundaries
- audit
- safe side effects
