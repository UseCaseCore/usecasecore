# MoveInventory

`MoveInventory` is the canonical UseCaseCore example because it looks small at
the UI layer and stops being small the moment it touches real state.

Moving inventory from one bin to another is not just "update a row." The action
has to validate the request, load the current balances, enforce permissions,
prevent invalid state transitions, commit related writes together, record an
audit trail, publish an event, queue follow-up work, and make retries safe.

UseCaseCore makes those responsibilities visible in one execution boundary.
The command layer Python apps keep rebuilding by accident.

```text
MoveInventoryCommand
  -> validate
  -> check idempotency
  -> load source + destination balances
  -> check policy
  -> check transitions and invariants
  -> open transaction
  -> apply balance changes + movement history
  -> write audit
  -> emit InventoryMoved
  -> queue LowStockAlert
  -> remember result
  -> MoveInventoryResult
```

UseCaseCore makes this path explicit and reusable instead of re-implementing it
in every service.

This in-memory example teaches the action lifecycle. For a realistic FastAPI +
SQLAlchemy version with database tables, idempotency records, audit rows, and
outbox records, see
[`examples/fastapi_sqlalchemy_inventory`](https://github.com/UseCaseCore/usecasecore/tree/main/examples/fastapi_sqlalchemy_inventory).

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

## Before / After: the route handler problem

Stop hiding business mutations in FastAPI routes.

In a typical FastAPI application, `MoveInventory` starts as a route and slowly
turns into a service layer by accident. The route receives the request, reaches
for the database session, loads rows, checks permissions, updates balances,
writes history, publishes signals, queues follow-up jobs, remembers idempotency,
and shapes the response.

```python
@app.post("/inventory/move")
def move_inventory(request: MoveInventoryRequest, session: Session = Depends(get_session)):
    # validate request
    # load source and destination balances
    # check permissions
    # check inventory invariants
    # update balances
    # create movement history
    # write audit
    # publish event
    # enqueue low-stock job
    # remember idempotency
    # return response
```

That works until the same action must also run from a worker, a retry path, an
admin tool, or another internal workflow. The mutation boundary is now hidden in
transport code.

With UseCaseCore, the route only translates HTTP input into a command and maps
the typed result back to HTTP output.

```python
@app.post("/inventory/move")
def move_inventory(request: MoveInventoryRequest):
    command = request.to_command()
    result = move_inventory_use_case.execute(command)
    return MoveInventoryResponse.from_result(result)
```

The route is now transport glue. The use case is the authoritative business
mutation boundary.

```text
validate -> idempotency -> load state -> policy -> transitions -> transaction -> apply -> audit -> events -> jobs -> result
```

FastAPI standardizes the API layer. SQLAlchemy standardizes persistence.
UseCaseCore standardizes the business action boundary: a standard execution
spine for Python backend mutations.

## Command creation

The command is the boundary where business intent enters the application. It is
not a database model and it is not a route handler payload after the handler has
started doing work. It is the typed request to perform one action.

```python
from dataclasses import dataclass


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
```

The `request_id` is useful for tracing. The `idempotency_key` makes retried
requests safe. The remaining fields describe the inventory move itself.

## Execution call

An API route, background job, or internal caller creates the command and hands it
to the use case. The caller does not open the transaction, write audit records,
publish events, or decide how retries are remembered.

```python
from examples.move_inventory import (
    InMemoryInventoryRepository,
    MoveInventoryCommand,
    MoveInventoryUseCase,
)
from usecasecore import InMemoryIdempotencyStore

repository = InMemoryInventoryRepository()
repository.set_balance("sku-1", "A", 10, low_stock_threshold=6)
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

The result is typed and stable:

```python
assert result.success is True
assert result.movement_id == "movement-1"
assert result.source_qty_after == 6
assert result.dest_qty_after == 5
```

## Request lifecycle

### 1. Validation

Cheap command-level checks happen before state is loaded. In this example, the
quantity must be positive and the source and destination bins must differ.

```python
def validate(self, command: MoveInventoryCommand) -> None:
    if command.qty <= 0:
        raise ValidationFailed("qty must be greater than zero")
    if command.from_bin_id == command.to_bin_id:
        raise ValidationFailed("source and destination bins must differ")
```

These are not database concerns. They are request sanity checks.

### 2. Idempotency

After validation, the base `UseCase` checks whether this command already
completed.

```text
idempotency_key -> stored result -> return without mutating state again
```

If the key exists, the previous `MoveInventoryResult` is returned. The source
balance is not decremented twice, movement history is not duplicated, and
downstream signals are not re-enqueued.

The in-memory store is deliberately small:

```python
class InMemoryIdempotencyStore:
    def get(self, key: str) -> object | None:
        return self._results.get(key)

    def save(self, key: str, result: object) -> None:
        existing = self._results.get(key)
        if existing is not None and existing != result:
            raise IdempotencyConflict(f"idempotency key already used: {key}")
        self._results[key] = result
```

Real systems usually back this with a database table and a uniqueness
constraint.

### 3. State loading

Inventory moves are write paths that still need reads first. The use case loads
the exact current state the write depends on.

```python
def load_state(self, command: MoveInventoryCommand) -> MoveInventoryState:
    return MoveInventoryState(
        source=self.repository.get_balance_for_update(
            command.product_id,
            command.from_bin_id,
        ),
        destination=self.repository.get_balance_for_update(
            command.product_id,
            command.to_bin_id,
        ),
    )
```

The repository method name is intentional. In a real store,
`get_balance_for_update()` is where row locking or equivalent consistency rules
would live.

### 4. Policy check

Policy checks answer whether this actor may perform this action. The example
keeps the rule minimal: a move must have an actor.

```python
def check_policies(
    self,
    command: MoveInventoryCommand,
    state: MoveInventoryState | None,
) -> None:
    if not command.moved_by_user_id:
        raise PolicyDenied("moved_by_user_id is required to move inventory")
```

Production applications can replace this with an adapter to a policy engine or
their own authorization service. The use case boundary stays the same.

### 5. Transition and invariant check

Transition checks decide whether the loaded state allows the requested action.
For inventory, the basic invariants are concrete:

- the source balance must exist
- the destination balance must exist
- the source must have enough quantity
- the move must not create negative inventory

```python
def check_transitions(
    self,
    command: MoveInventoryCommand,
    state: MoveInventoryState | None,
) -> None:
    if state is None:
        raise TransitionDenied("inventory state was not loaded")
    if state.source is None:
        raise TransitionDenied("source balance does not exist")
    if state.destination is None:
        raise TransitionDenied("destination balance does not exist")
    if state.source.qty < command.qty:
        raise TransitionDenied("source bin does not have enough inventory")
    if state.source.qty - command.qty < 0:
        raise TransitionDenied("move would create negative inventory")
```

This is the difference between accepting a request and allowing it to change
truth.

### 6. Transaction boundary

The base `UseCase.execute()` opens the transaction after validation,
idempotency, state loading, policy checks, and transition checks have passed.

```python
with self.transaction():
    result = self.apply(command, state)
    self.write_audit(command, state, result)
    self.emit_events(command, state, result)
    self.enqueue_jobs(command, state, result)
    self.remember_idempotency(command, result)
```

The example uses the default no-op transaction manager for in-memory tests. A
real application would provide a transaction manager backed by SQLAlchemy,
SQLModel, or another persistence layer.

### 7. Apply state changes

`apply()` performs the authoritative mutation. The use case delegates the
persistence details to the repository and returns a typed result.

```python
def apply(
    self,
    command: MoveInventoryCommand,
    state: MoveInventoryState | None,
) -> MoveInventoryResult:
    if state is None or state.source is None or state.destination is None:
        raise TransitionDenied("inventory state was not loaded")

    movement, source, destination = self.repository.move(
        command,
        source=state.source,
        destination=state.destination,
    )
    return MoveInventoryResult(
        success=True,
        movement_id=movement.movement_id,
        product_id=command.product_id,
        from_bin_id=command.from_bin_id,
        to_bin_id=command.to_bin_id,
        quantity_moved=command.qty,
        source_qty_after=source.qty,
        dest_qty_after=destination.qty,
    )
```

The repository keeps balance updates and movement history together:

```python
def move(
    self,
    command: MoveInventoryCommand,
    source: InventoryBalance,
    destination: InventoryBalance,
) -> tuple[InventoryMovement, InventoryBalance, InventoryBalance]:
    source_after = replace(source, qty=source.qty - command.qty)
    destination_after = replace(destination, qty=destination.qty + command.qty)
    self.save_balance(source_after)
    self.save_balance(destination_after)
    movement = self.create_movement(
        command,
        source_after=source_after,
        destination_after=destination_after,
    )
    return movement, source_after, destination_after
```

The in-memory implementation is only a teaching adapter. The important boundary
is the repository protocol: the use case owns the action order, while the
repository owns persistence details.

### 8. Audit

After the mutation succeeds, the use case writes an audit entry describing who
changed what and why.

```python
self.audit_sink.write(
    AuditEntry(
        action="MoveInventory",
        actor_id=command.moved_by_user_id,
        payload={
            "request_id": command.request_id,
            "movement_id": result.movement_id,
            "product_id": command.product_id,
            "from_bin_id": command.from_bin_id,
            "to_bin_id": command.to_bin_id,
            "qty": command.qty,
            "reason": command.reason,
        },
    )
)
```

Audit is not scattered across route handlers or repository methods. It is part
of the business action lifecycle.

### 9. Event emission

The use case emits a domain event after truth has been updated.

```python
self.event_bus.publish(
    InventoryMoved(
        movement_id=result.movement_id,
        request_id=command.request_id,
        product_id=command.product_id,
        from_bin_id=command.from_bin_id,
        to_bin_id=command.to_bin_id,
        qty=command.qty,
        moved_by_user_id=command.moved_by_user_id,
    )
)
```

The event says what happened. It does not decide which downstream systems care.

### 10. Job enqueueing

The example queues a `LowStockAlert` job when the source bin falls to or below
its threshold.

```python
threshold = state.source.low_stock_threshold
if threshold is None:
    threshold = self.default_low_stock_threshold

if threshold is not None and result.source_qty_after <= threshold:
    self.job_queue.enqueue(
        LowStockAlert(
            product_id=command.product_id,
            bin_id=command.from_bin_id,
            remaining_qty=result.source_qty_after,
            threshold=threshold,
        )
    )
```

The job is explicit follow-up work. It is not hidden in a model method or tacked
onto an API route after the response is assembled.

### 11. Typed result

The caller receives a `MoveInventoryResult` instead of an ad hoc response shape.

```python
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
```

The result is stable enough for API responses, tests, idempotency replay, and
internal callers.

## Why this is not just CRUD

CRUD describes simple persistence operations. `MoveInventory` is not a CRUD
example. It is a state-changing business action with multiple invariants and
side effects.

A CRUD implementation might update a balance row. A real inventory move has to
coordinate multiple concerns:

- validate the requested move
- read the current source and destination state
- prevent negative inventory
- enforce actor permissions
- update both balances together
- create movement history
- produce an audit trail
- emit a domain event
- queue low-stock follow-up work
- return the same result for safe retries

Those concerns belong in one visible execution model. UseCaseCore gives the
action a standard shape without deciding the domain meaning for you.

## What this example intentionally does not solve yet

This example is intentionally small. It demonstrates the execution boundary, not
every production integration.

It does not yet provide:

- real database persistence
- SQLAlchemy or SQLModel integration
- an outbox pattern for durable event publishing
- async workers or async use cases
- distributed locks

Those are integration layers that can be added around the same command and use
case shape. The point of the example is to make the action boundary clear before
adding infrastructure-specific adapters.
