from __future__ import annotations

from typing import Protocol


class Repository(Protocol):
    """Marker protocol for persistence boundaries used by a use case."""
