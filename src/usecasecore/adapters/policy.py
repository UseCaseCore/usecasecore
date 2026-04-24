from __future__ import annotations

from typing import Protocol

from usecasecore.context import ExecutionContext


class PolicyAdapter(Protocol):
    """Adapter boundary for authorization engines and policy services."""

    def allowed(
        self,
        command: object,
        state: object,
        context: ExecutionContext,
    ) -> bool:
        """Return whether the actor may perform this action."""


class AllowAllPolicy:
    """Development policy adapter that allows every action."""

    def allowed(
        self,
        command: object,
        state: object,
        context: ExecutionContext,
    ) -> bool:
        return True
