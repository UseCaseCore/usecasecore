# FastAPI + SQLAlchemy Inventory Example

This example shows UseCaseCore in a realistic Python backend stack.

It keeps the FastAPI route small and puts the state-changing business action in
a use case:

```text
FastAPI route
  -> Pydantic request
  -> MoveInventoryCommand
  -> MoveInventoryUseCase
  -> SQLAlchemy repository
  -> transaction
  -> inventory_movements + audit_records + outbox_records + idempotency_records
  -> Pydantic response
```

The FastAPI route is transport glue.
The use case is the business mutation boundary.
SQLAlchemy owns persistence.
UseCaseCore owns the action lifecycle.

## Install dependencies

From the repository root:

```bash
pip install -e ".[dev,fastapi,sqlalchemy,pydantic]"
```

SQLite is used for the demo and tests so you do not need Docker.

## Run the tests

```bash
python3 -m pytest tests/examples/test_fastapi_sqlalchemy_inventory.py
```

## Request

```http
POST /inventory/move
```

```json
{
  "request_id": "req-1",
  "idempotency_key": "move-sku-1-A-B-4",
  "product_id": "sku-1",
  "from_bin_id": "A",
  "to_bin_id": "B",
  "qty": 4,
  "moved_by_user_id": "user-1",
  "reason": "rebalancing"
}
```

## Response

```json
{
  "success": true,
  "movement_id": "movement-1",
  "product_id": "sku-1",
  "from_bin_id": "A",
  "to_bin_id": "B",
  "quantity_moved": 4,
  "source_qty_after": 6,
  "dest_qty_after": 5
}
```

## Why this is not CRUD

Moving inventory is not a single update. The action needs validation,
idempotency, current-state reads, permission checks, invariant checks, a
transaction boundary, movement history, audit, outbox events, optional follow-up
jobs, and a typed result.

UseCaseCore gives that mutation path one explicit execution spine instead of
letting it accumulate inside a FastAPI route.

## What changes for Postgres production use

For production, keep the same command and use-case shape but replace the demo
infrastructure:

- replace the SQLite URL with a Postgres URL
- use real migrations with Alembic
- use `SELECT FOR UPDATE` / row locking where appropriate
- put unique constraints on idempotency keys and inventory balance identity
- have a dispatcher consume `outbox_records` after commit
