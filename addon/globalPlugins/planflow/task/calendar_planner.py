
"""
CalendarPlanner: Computes valid scheduling windows for tasks, enforcing working hours, slot preferences, and per-day limits.

This module provides logic to validate and compute valid scheduling windows for tasks, enforcing working hours, daily limits, and slot preferences.
"""


from __future__ import annotations
from datetime import datetime, timedelta
from .task_model import TaskOccurrence, WorkingHours, TimeSlot


class CalendarPlanner:
    """Encapsulates availability logic for scheduling tasks based on user constraints.

    Enforces working hours, slot preferences, and per-day task limits.
    """

    SEARCH_WINDOW_DAYS: int = 14

    def is_slot_available(
        self,
        proposed_time: datetime,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        max_per_day: int,
        slot_pool: list[TimeSlot] | None = None
    ) -> bool:
        """Check if a new task can be scheduled at the proposed time.

        Args:
            proposed_time: The datetime to test availability for.
            scheduled_occurrences: List of already scheduled TaskOccurrence.
            working_hours: List of WorkingHours objects for allowed scheduling per weekday.
            max_per_day: Maximum allowed tasks per calendar day.

        Returns:
            True if the slot is available (within working hours, not exceeding per-day cap, and not colliding with existing tasks), else False.

        Fallback:
            Returns False if the day is not in working_hours or slot is not allowed.
        """
        day = proposed_time.date()
        weekday = proposed_time.strftime("%A").lower()
        # Find working hours for this weekday
        wh: WorkingHours | None = next((w for w in working_hours if w.day == weekday), None)
        if wh is None:
            return False
        # Check if within working hours
        if not (wh.start <= proposed_time.time() <= wh.end):
            return False
        # Per-day cap
        count = sum(1 for occ in scheduled_occurrences if occ.scheduled_for.date() == day)
        if count >= max_per_day:
            return False
        # No collision (same time)
        if any(occ.scheduled_for == proposed_time for occ in scheduled_occurrences):
            return False
        # Must be in allowed_slots for that day if specified
        if wh.allowed_slots:
            if slot_pool is None:
                return False
            # Find a slot in slot_pool that matches proposed_time and is allowed
            slot_match = False
            for slot in slot_pool:
                if slot.name in wh.allowed_slots and slot.start == proposed_time.time():
                    slot_match = True
                    break
            if not slot_match:
                return False
        return True

    def next_available_slot(
        self,
        after: datetime,
        slot_pool: list[TimeSlot],
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        max_per_day: int,
        priority: int | None = None
    ) -> datetime | None:
        """Find the next available valid datetime for scheduling.

        Args:
            after: The datetime after which to search for availability.
            slot_pool: List of allowed TimeSlot objects (user preferences).
            scheduled_occurrences: List of already scheduled TaskOccurrence.
            working_hours: List of WorkingHours objects for allowed scheduling per weekday.
            max_per_day: Maximum allowed tasks per calendar day.
            priority: Optional integer to affect slot ordering (lower = higher priority).

        Returns:
            The first available datetime matching all constraints, or None if not found within 14 days.

        Fallback:
            Returns None if no valid slot is found within the search window.
        """
        search_start = after + timedelta(minutes=1)
        for day_offset in range(self.SEARCH_WINDOW_DAYS):
            candidate_date = (search_start + timedelta(days=day_offset)).date()
            weekday = candidate_date.strftime("%A").lower()
            wh: WorkingHours | None = next((w for w in working_hours if w.day == weekday), None)
            if wh is None:
                continue  # skip holidays or days with no working hours
            # Filter slots within working hours and allowed_slots
            slots_today = [
                slot for slot in slot_pool
                if (
                    wh.start <= slot.start <= wh.end
                    and (not wh.allowed_slots or slot.name in wh.allowed_slots)
                )
            ]
            # Sort slots by priority if provided
            if priority is not None and 0 <= priority < len(slots_today):
                slots_today = slots_today[priority:] + slots_today[:priority]
            for slot in slots_today:
                candidate_dt = datetime.combine(candidate_date, slot.start)
                if candidate_dt <= after:
                    continue
                if self.is_slot_available(candidate_dt, scheduled_occurrences, working_hours, max_per_day, slot_pool):
                    return candidate_dt
        return None
