# Architecture

```text
FastAPI
  ↓
Command model
  ↓
UseCaseCore
  ↓
Repositories / Session
  ↓
SQLModel / SQLAlchemy
  ↓
Postgres
  ↓
Alembic evolves schema
```

## Layers

### API
FastAPI routes receive requests and produce validated commands.

### UseCaseCore
The service runtime for business actions.

Core modules:

- `usecasecore.usecase`
- `usecasecore.context`
- `usecasecore.transaction`
- `usecasecore.audit`
- `usecasecore.idempotency`
- `usecasecore.events`
- `usecasecore.jobs`

The base runtime can:

- replay completed results from an idempotency store
- run authoritative changes inside a transaction manager
- write audit entries through an audit sink
- publish events through an event bus
- enqueue follow-up work through a job queue

### Repositories
Persistence boundaries around SQLAlchemy / SQLModel sessions.

### Database
Postgres remains the source of truth.

### Schema evolution
Alembic manages migrations.
