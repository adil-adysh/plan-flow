"""CalendarPlanner: Enforces per-day task limits and computes available scheduling slots.

This module provides logic to validate and compute available scheduling slots for tasks, enforcing constraints like maximum tasks per day, conflict avoidance, and rescheduling availability.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from .task_model import TaskOccurrence

class CalendarPlanner:
    """Encapsulates task scheduling constraints and availability for PlanFlow tasks.

    Provides methods to check slot availability and compute the next available day for scheduling.
    """

    SEARCH_WINDOW_DAYS: int = 30  # Internal limit for next_available_day search

    def is_slot_available(
        self,
        proposed_time: datetime,
        scheduled_occurrences: list[TaskOccurrence],
        max_per_day: int
    ) -> bool:
        """Check if a new task can be scheduled at the given time.

        Args:
            proposed_time: The datetime to test availability for.
            scheduled_occurrences: All current task occurrences (future or pending).
            max_per_day: Maximum allowed tasks per day.

        Returns:
            True if fewer than max_per_day tasks are scheduled for the day of proposed_time.
        """
        day = proposed_time.date()
        count = sum(1 for occ in scheduled_occurrences if occ.scheduled_for.date() == day)
        return count < max_per_day

    def next_available_day(
        self,
        after: datetime,
        scheduled_occurrences: list[TaskOccurrence],
        max_per_day: int
    ) -> datetime | None:
        """Return the next datetime where a slot is available for scheduling.

        Args:
            after: The datetime after which to search for availability.
            scheduled_occurrences: All current task occurrences (future or pending).
            max_per_day: Maximum allowed tasks per day.

        Returns:
            The next datetime with an available slot, or None if not found within the search window.
        """
        for offset in range(1, self.SEARCH_WINDOW_DAYS + 1):
            candidate = after + timedelta(days=offset)
            if self.is_slot_available(candidate, scheduled_occurrences, max_per_day):
                return candidate
        return None
