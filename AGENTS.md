# AGENTS.md

## Project
UseCaseCore — the standard runtime for application use cases.

## Positioning
UseCaseCore standardizes the service layer between validated input and committed truth.

## Tone
Boring, explicit, enterprise-grade Python infrastructure. No hype.

## Core execution flow
Command -> validate -> idempotency -> load state -> policies -> transitions -> transaction -> apply -> audit -> events -> jobs -> result.

## Design rules
- Keep core small.
- No hard dependency on FastAPI, SQLAlchemy, Pydantic, Oso, Temporal, or queue engines.
- Use adapters and Protocols for integrations.
- Prefer dataclasses and typing for the core.
- Make the API obvious and testable.
- The canonical example is MoveInventory.
- Avoid framework magic.

## Public API target
from usecasecore import Command, Result, ExecutionContext, UseCase

## Tests
Use pytest.
Verify execution lifecycle order, error propagation, idempotency behavior, and MoveInventory example behavior.

## Docs
Write direct, concrete docs.
Use MoveInventory as the primary teaching example.

## Do not
- overbuild
- add hidden globals
- introduce unnecessary dependencies
- turn this into a BPM engine
- claim maturity that does not exist
