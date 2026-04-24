from __future__ import annotations

from typing import Protocol

from usecasecore.context import ExecutionContext


class TransitionAdapter(Protocol):
    """Adapter boundary for state machines and lifecycle rules."""

    def allowed(
        self,
        command: object,
        state: object,
        context: ExecutionContext,
    ) -> bool:
        """Return whether this state transition is allowed."""


class AllowAllTransitions:
    """Development transition adapter that allows every transition."""

    def allowed(
        self,
        command: object,
        state: object,
        context: ExecutionContext,
    ) -> bool:
        return True
