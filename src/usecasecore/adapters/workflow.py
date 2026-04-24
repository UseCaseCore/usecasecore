from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class WorkflowAdapter(Protocol):
    """Adapter boundary for long-running workflow engines."""

    def start(self, workflow_name: str, payload: Mapping[str, object]) -> str:
        """Start a workflow and return its external id."""
