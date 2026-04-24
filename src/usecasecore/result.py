from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Generic, TypeVar

ValueT = TypeVar("ValueT")


@dataclass(frozen=True, slots=True)
class Result(Generic[ValueT]):
    """Typed use-case result with optional side-effect metadata."""

    value: ValueT
    events: tuple[object, ...] = ()
    jobs: tuple[object, ...] = ()
    audit: Mapping[str, object] | None = None

    @classmethod
    def ok(cls, value: ValueT) -> "Result[ValueT]":
        return cls(value=value)

    def with_event(self, event: object) -> "Result[ValueT]":
        return replace(self, events=(*self.events, event))

    def with_job(self, job: object) -> "Result[ValueT]":
        return replace(self, jobs=(*self.jobs, job))

    def with_audit(self, audit: Mapping[str, object]) -> "Result[ValueT]":
        return replace(self, audit=audit)
