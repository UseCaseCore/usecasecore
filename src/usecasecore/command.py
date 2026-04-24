from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Command(Protocol):
    """Marker protocol for typed business intent."""
