# Concepts

## Command

Typed business intent. A command says what the caller wants to do.

## Use case

The execution boundary for one business action.

## Execution context

Runtime metadata for one execution, such as request id, actor id, correlation
id, tenant id, idempotency key, start time, and caller metadata.

## State

The current domain data the action depends on.

## Policy and transitions

Policy answers whether the actor may perform the action. Transitions answer
whether the current state can move through the requested action.

## Transaction

The visible boundary where authoritative changes are written.

## Idempotency

An idempotency key lets the runtime replay a completed result instead of running
the same state-changing action twice.

## Audit, events, and jobs

Audit records who changed what. Events describe what happened. Jobs perform
explicit follow-up work after truth has been updated.

Use cases can implement these hooks directly, or return a `Result` with audit,
event, and job metadata for the base runtime to dispatch through configured
sinks.
