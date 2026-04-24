# Contributing

UseCaseCore is the standard runtime for application use cases.

It standardizes the service layer between validated input and committed truth:
commands, state loading, policy checks, transitions, transactions, audit,
idempotency, events, jobs, and typed results.

## Local Development

Create a virtual environment, then install the package with development tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Tests

Run the full test suite with pytest:

```bash
python -m pytest
```

The tests can also run with the standard library test runner:

```bash
env PYTHONPATH=src:. python3 -m unittest discover tests
env PYTHONPATH=src:. python3 -m unittest discover tests/examples
```

Run a compile check before opening a PR:

```bash
python3 -m compileall src examples tests
```

## Linting

Run Ruff:

```bash
python -m ruff check .
```

## Design Principles

- Keep the core small and explicit.
- Prefer dataclasses, Protocols, and typed boundaries.
- Do not add hard dependencies on FastAPI, SQLAlchemy, Pydantic, Oso, Temporal,
  or queue engines.
- Use adapters for integrations.
- Keep `MoveInventory` as the canonical teaching example.
- Choose readable override methods over framework magic.

## Pull Requests

Small PRs are preferred. Each PR should make one clear improvement and include
tests when it changes runtime behavior.
