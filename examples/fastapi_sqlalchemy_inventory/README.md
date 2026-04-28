# FastAPI + SQLAlchemy Inventory Example

This example shows UseCaseCore in a realistic Python backend stack.

It is intentionally small: one endpoint, one command, one use case, one
SQLAlchemy repository, and a few tables that make the mutation path visible.
The point is not to build a full inventory system. The point is to show the
transaction-safe command layer Python apps keep rebuilding by accident.

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

## What this example proves

- The route stays small.
- Mutation logic is outside FastAPI.
- The SQLAlchemy session commits at the use-case boundary.
- Reusing an idempotency key returns the same result without duplicate writes.
- Audit and outbox records are written with the mutation.
- Failed transitions return safe errors before state changes.

## How the route stays small

The route receives HTTP input, creates a command, executes the use case, and
maps the typed result back to an HTTP response.

```python
@app.post("/inventory/move", response_model=MoveInventoryResponse)
def move_inventory(
    request: MoveInventoryRequest,
    session: Session = Depends(get_session),
) -> MoveInventoryResponse:
    use_case = MoveInventoryUseCase(
        repository=SQLAlchemyInventoryRepository(session),
        idempotency_store=SQLAlchemyIdempotencyStore(session),
        audit_sink=SQLAlchemyAuditSink(session),
        event_bus=SQLAlchemyOutboxEventBus(session),
        job_queue=SQLAlchemyOutboxJobQueue(session),
        transaction_manager=SQLAlchemyTransactionManager(session),
    )

    result = use_case.execute(request.to_command())
    return MoveInventoryResponse.from_result(result)
```

The route does not load rows, mutate balances, write audit records, publish
events, enqueue jobs, or remember idempotency results.

## How the use case owns the mutation

`MoveInventoryUseCase` owns the business action lifecycle:

```text
validate -> idempotency -> load state -> policy -> transitions -> transaction -> apply -> audit -> outbox -> jobs -> result
```

That lifecycle handles:

- `qty <= 0` validation
- same-bin validation
- current source and destination balance loading
- actor presence as a simple policy check
- missing balance and insufficient inventory transition checks
- authoritative balance updates
- movement history
- audit record creation
- outbox event creation
- low-stock job creation
- idempotency replay without duplicate writes

## How SQLAlchemy persistence is wired

The example uses SQLite so it can run without Docker, but the table boundaries
are the ones a Postgres app would expect:

- `inventory_balances`
- `inventory_movements`
- `idempotency_records`
- `audit_records`
- `outbox_records`

The repository handles state loading and balance mutation:

```python
source = repository.get_balance_for_update(product_id="sku-1", bin_id="A")
destination = repository.get_balance_for_update(product_id="sku-1", bin_id="B")
```

In Postgres, `get_balance_for_update()` is where row locking belongs. In this
demo it is still named that way so the upgrade path is obvious.

The transaction manager commits or rolls back the SQLAlchemy session around the
use-case boundary:

```python
with self.transaction():
    result = self.apply(command, state)
    self.write_audit(command, state, result)
    self.emit_events(command, state, result)
    self.enqueue_jobs(command, state, result)
    self.remember_idempotency(command, result)
```

## How idempotency replay works

`SQLAlchemyIdempotencyStore` stores the completed response as JSON by
idempotency key.

On retry:

```text
same idempotency_key -> stored MoveInventoryResult -> return response
```

The tests prove the replay behavior:

- the second request returns the same response
- no second movement row is created
- source inventory is not decremented twice
- no duplicate audit or outbox rows are created

## How audit and outbox records are written

The use case writes audit and outbox records inside the same lifecycle as the
mutation:

- `SQLAlchemyAuditSink` writes `audit_records`
- `SQLAlchemyOutboxEventBus` writes `InventoryMoved` to `outbox_records`
- `SQLAlchemyOutboxJobQueue` writes `LowStockAlert` to `outbox_records`

This keeps audit and outbox records written with the mutation instead of being
scattered across route handlers or model methods.

## Read the code in this order

1. `schemas.py` - HTTP request/response shape
2. `app.py` - FastAPI route as transport glue
3. `usecases.py` - business mutation boundary
4. `repositories.py` - SQLAlchemy persistence adapters
5. `models.py` - database tables
6. `transaction.py` - commit/rollback boundary
7. `tests/examples/test_fastapi_sqlalchemy_inventory.py` - proof of behavior

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
