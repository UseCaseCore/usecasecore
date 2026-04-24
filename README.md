# UseCaseCore

The standard runtime for application use cases.

UseCaseCore gives business actions one explicit, typed, transactional execution
model across validation, state loading, policy checks, transitions, audit,
idempotency, events, and side effects.

## Why

Your API layer is standardized. Your data layer is standardized. Your service
layer is still where business logic leaks into routes, model methods, jobs, and
helpers.

UseCaseCore standardizes that missing layer without replacing FastAPI,
SQLModel, SQLAlchemy, Postgres, Alembic, Oso, pytransitions, Temporal, or the
stack you already use.

## Install

```bash
pip install usecasecore
```

## Core path

```text
command
  -> validate
  -> check idempotency
  -> load state
  -> check policy
  -> check transitions
  -> open transaction
  -> apply changes
  -> write audit
  -> emit events
  -> queue side effects
  -> return result
```

## Quick example

```python
from examples.move_inventory import (
    InMemoryInventoryRepository,
    MoveInventoryCommand,
    MoveInventoryUseCase,
)
from usecasecore import InMemoryIdempotencyStore

repo = InMemoryInventoryRepository()
repo.set_balance(product_id="sku-1", bin_id="A", qty=10)
repo.set_balance(product_id="sku-1", bin_id="B", qty=1)

use_case = MoveInventoryUseCase(
    repository=repo,
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

## Current v0.1.0 surface

- `UseCase` execution shell with validation, state loading, policy checks,
  transitions, transactions, audit, events, jobs, and idempotency.
- `Result` wrapper for use cases that want to return metadata for default
  audit/event/job dispatch.
- In-memory audit, event, job, and idempotency implementations for examples and
  tests.
- Adapter protocols for policy engines, state machines, workflow engines, event
  buses, and job queues.
- Canonical `MoveInventory` example with validation, repository state loading,
  policy checks, invariant checks, audit, events, jobs, and idempotency replay.

## Where it fits

```text
FastAPI
  -> Command model
  -> UseCaseCore
  -> Repositories / Session
  -> SQLModel / SQLAlchemy
  -> Postgres

Alembic evolves schema.
```

## What it is not

- not an API framework
- not an ORM
- not a database
- not a migration tool
- not a BPM suite
- not a no-code workflow builder
- not a universal rules engine

## Repository layout

```text
src/usecasecore/          core package
src/usecasecore/adapters/ adapter protocols
examples/move_inventory/ canonical example
docs/                     documentation stubs
tests/                    lifecycle and example tests
index.html                homepage
```

## Docs and Examples

- [Quickstart](docs/quickstart.md)
- [Concepts](docs/concepts.md)
- [Architecture](docs/architecture.md)
- [Adapters](docs/adapters.md)
- [MoveInventory example](docs/examples/move-inventory.md)
- [Example source](examples/move_inventory)

## Release Process

Publishing is manual for now. Do not upload to PyPI until CI is green.

Build and check the package:

```bash
rm -rf build dist src/usecasecore.egg-info
python3 -m build
python3 -m twine check dist/*
```

For TestPyPI, upload with a TestPyPI token:

```bash
python3 -m twine upload --repository testpypi dist/*
```

Then verify install in a clean environment:

```bash
python3 -m venv /tmp/ucc-test
source /tmp/ucc-test/bin/activate
python3 -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  usecasecore
python3 -c "from usecasecore import Command, Result, ExecutionContext, UseCase; print('OK')"
deactivate
```

Only publish to PyPI after the TestPyPI install works.

## Status

Early alpha moving toward `v0.1.0`. The core abstractions are intentionally
small while the execution model settles.
