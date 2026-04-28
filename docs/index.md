# UseCaseCore Docs

UseCaseCore is the standard runtime for application use cases.

It gives each business action one explicit path from typed intent to committed
truth:

```text
command -> idempotency -> state -> policy -> transaction -> audit -> events -> jobs -> result
```

## Start here

- [Quickstart](quickstart.md)
- [Concepts](concepts.md)
- [Architecture](architecture.md)
- [Adapters](adapters.md)
- [MoveInventory example](examples/move-inventory.md)
- [FastAPI + SQLAlchemy inventory example](https://github.com/UseCaseCore/usecasecore/tree/main/examples/fastapi_sqlalchemy_inventory)
