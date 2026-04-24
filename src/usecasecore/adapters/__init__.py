"""Adapter protocols for optional integrations."""

from .event_bus import EventBusAdapter
from .job_queue import JobQueueAdapter
from .policy import AllowAllPolicy, PolicyAdapter
from .transitions import AllowAllTransitions, TransitionAdapter
from .workflow import WorkflowAdapter

__all__ = [
    "AllowAllPolicy",
    "AllowAllTransitions",
    "EventBusAdapter",
    "JobQueueAdapter",
    "PolicyAdapter",
    "TransitionAdapter",
    "WorkflowAdapter",
]
