# MoveInventory

This example shows one real action end to end:

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

Use it as the canonical walkthrough for the first public docs.

The example also accepts an `IdempotencyStore`, so retries with the same command
key replay the first result instead of applying the movement again.
