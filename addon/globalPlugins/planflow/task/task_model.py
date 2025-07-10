"""Task model definitions for PlanFlow NVDA add-on.

This module defines core data models for the PlanFlow task scheduler. All models are logic-free, testable, and serializable for TinyDB.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal

__all__ = [
    "TaskDefinition",
    "RetryPolicy",
    "TaskOccurrence",
    "TaskExecution",
    "TaskEvent",
]

@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Defines retry behavior for a task.

    Attributes:
        max_retries: Total number of retry attempts allowed.
        retry_interval: Time delay between retries.
        speak_on_retry: Whether NVDA should speak the task on retry.
    """
    max_retries: int
    retry_interval: timedelta
    speak_on_retry: bool = True

@dataclass(frozen=True, slots=True)
class TaskDefinition:
    """Represents a user-configured task.

    Attributes:
        id: Unique identifier for the task.
        title: Task title.
        description: Optional description.
        link: Optional URL or file path.
        created_at: Creation timestamp.
        recurrence: Optional recurrence interval.
        retry_policy: Retry policy for missed/failing tasks.
    """
    id: str
    title: str
    description: str | None
    link: str | None
    created_at: datetime
    recurrence: timedelta | None
    retry_policy: RetryPolicy

@dataclass(frozen=True, slots=True)
class TaskOccurrence:
    """Represents a scheduled instance of a task.

    Attributes:
        id: Unique identifier for this occurrence.
        task_id: The parent task's id.
        scheduled_for: When this occurrence is scheduled.
    """
    id: str
    task_id: str
    scheduled_for: datetime

@dataclass(frozen=True, slots=True)
class TaskEvent:
    """Append-only event log used in TaskExecution history.

    Attributes:
        event: Event type (triggered, missed, rescheduled, completed).
        timestamp: When the event occurred.
    """
    event: Literal["triggered", "missed", "rescheduled", "completed"]
    timestamp: datetime

@dataclass(frozen=True, slots=True)
class TaskExecution:
    """Tracks the runtime status of a task occurrence.

    Attributes:
        occurrence_id: The id of the related TaskOccurrence.
        state: Current state (pending, done, missed, cancelled).
        retries_remaining: How many retries are left.
        history: List of TaskEvent objects.
    """
    occurrence_id: str
    state: Literal["pending", "done", "missed", "cancelled"]
    retries_remaining: int
    history: list["TaskEvent"] = field(default_factory=list)  # type: ignore[type-arg]

    @property
    def is_reschedulable(self) -> bool:
        """Whether the task can be rescheduled (if retries remain)."""
        return self.retries_remaining > 0 and self.state in ("missed", "pending")

    @property
    def retry_count(self) -> int:
        """Number of retries already attempted."""
        if not self.history:
            return 0
        return sum(1 for e in self.history if e.event == "rescheduled")

    @property
    def last_event_time(self) -> datetime | None:
        """Timestamp of the most recent event, or None if no events."""
        if not self.history:
            return None
        return self.history[-1].timestamp
