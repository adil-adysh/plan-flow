"""Task model definitions for PlanFlow NVDA add-on.

This module defines core data models for the PlanFlow task scheduler. All models are logic-free, testable, and serializable for TinyDB.
"""


from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Literal


__all__ = [
    "TaskDefinition",
    "RetryPolicy",
    "TaskOccurrence",
    "TaskExecution",
    "TaskEvent",
    "TimeSlot",
    "WorkingHours",
]


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Defines the user's configuration for retrying missed tasks.

    Attributes:
        max_retries (int): Total number of retry attempts allowed.
    """
    max_retries: int


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    """Represents a user-defined task.

    Attributes:
        id (str): Unique identifier for the task.
        title (str): Task title.
        description (Optional[str]): Optional description.
        link (Optional[str]): Local file or URL.
        created_at (datetime): Creation timestamp.
        recurrence (Optional[timedelta]): Optional recurrence interval.
        priority (Literal["low", "medium", "high"]): Task priority.
        preferred_slots (list[str]): Names of preferred TimeSlots.
        retry_policy (RetryPolicy): Retry policy for missed tasks.
        pinned_time (Optional[datetime]): User-requested exact datetime for scheduling.
    """
    id: str
    title: str
    description: str | None
    link: str | None
    created_at: datetime
    recurrence: timedelta | None
    priority: Literal["low", "medium", "high"]
    preferred_slots: list[str]
    retry_policy: RetryPolicy
    pinned_time: datetime | None = None


@dataclass(frozen=True, slots=True)
class TaskOccurrence:
    """Represents a scheduled instance of a task.

    Attributes:
        id (str): Unique identifier for this occurrence.
        task_id (str): The parent task's id.
        scheduled_for (datetime): When this occurrence is scheduled.
        slot_name (Optional[str]): Name of the time slot used for this occurrence.
        pinned_time (Optional[datetime]): User-requested exact datetime (must be validated before use).
    """
    id: str
    task_id: str
    scheduled_for: datetime
    slot_name: str | None
    pinned_time: datetime | None


@dataclass(frozen=True, slots=True)
class TaskEvent:
    """A log entry in a task’s execution lifecycle.

    Attributes:
        event (Literal["triggered", "missed", "rescheduled", "completed"]): Event type.
        timestamp (datetime): When the event occurred.
    """
    event: Literal["triggered", "missed", "rescheduled", "completed"]
    timestamp: datetime



@dataclass(frozen=True, slots=True)
class TaskExecution:
    """Tracks the runtime execution of a TaskOccurrence.

    Attributes:
        occurrence_id (str): The id of the related TaskOccurrence.
        state (Literal["pending", "done", "missed", "cancelled"]): Current state.
        retries_remaining (int): How many retries are left.
        history (list[TaskEvent]): List of TaskEvent objects.
    """
    occurrence_id: str
    state: Literal["pending", "done", "missed", "cancelled"]
    retries_remaining: int
    history: list[TaskEvent] = field(default_factory=list)

    @property
    def is_reschedulable(self) -> bool:
        """Whether the task can be rescheduled (if retries remain).

        Returns:
            bool: True if the task can be rescheduled, else False.
        """
        return self.retries_remaining > 0 and self.state in ("missed", "pending")

    @property
    def retry_count(self) -> int:
        """Number of retries already attempted.

        Returns:
            int: The number of retries already attempted.
        """
        return sum(1 for e in self.history if e.event == "rescheduled")

    @property
    def last_event_time(self) -> datetime | None:
        """Timestamp of the most recent event, or None if no events.

        Returns:
            datetime | None: The timestamp of the last event, or None.
        """
        if not self.history:
            return None
        return self.history[-1].timestamp


@dataclass(frozen=True, slots=True)
class TimeSlot:
    """Represents a uniquely identified named time window for task delivery.

    Attributes:
        id (str): Unique identifier for the slot (UUID).
        name (str): Name of the time slot (may not be unique).
        start (time): Start time of the slot.
        end (time): End time of the slot.
    """
    id: str
    name: str
    start: time
    end: time


@dataclass(frozen=True, slots=True)
class WorkingHours:
    """Defines allowed scheduling hours per weekday.

    Attributes:
        day (Literal["monday", ..., "sunday"]): Day of the week.
        start (time): Start time for allowed scheduling.
        end (time): End time for allowed scheduling.
        allowed_slots (list[str]): Names of TimeSlots allowed on that day.
    """
    day: Literal[
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    ]
    start: time
    end: time
    allowed_slots: list[str]
