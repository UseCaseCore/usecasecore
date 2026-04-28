# Changelog

## 0.1.0a3

### Added

- Added FastAPI + SQLAlchemy inventory example showing UseCaseCore in a realistic Python backend stack.
- Added SQLAlchemy-backed inventory repository, transaction manager, idempotency store, audit sink, and outbox adapters inside the example.
- Added integration tests for successful inventory movement, idempotency replay, invalid quantity, insufficient inventory, and missing destination.
- Added homepage and README walkthroughs explaining the FastAPI route-as-transport-glue pattern.

### Changed

- Improved MoveInventory documentation to distinguish business actions from CRUD.
- Improved homepage positioning around FastAPI, Pydantic, SQLAlchemy, and UseCaseCore responsibilities.

## 0.1.0 - Unreleased

- Initial core execution shell
- Command / Result / ExecutionContext
- Transaction, audit, idempotency, event, job interfaces
- Adapter protocols
- MoveInventory canonical example
- Docs and homepage
