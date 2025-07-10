
"""
Task scheduling logic for PlanFlow NVDA add-on.

This module implements the TaskScheduler class, which encapsulates core scheduling, recurrence, and retry logic for tasks. All logic is pure, testable, and NVDA-independent.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from .task_model import (
    TaskDefinition,
    TaskOccurrence,
    TaskExecution,
    RetryPolicy,
    TimeSlot,
    WorkingHours,
)
from .calendar_planner import CalendarPlanner


class TaskScheduler:
    """Handles recurrence, retrying, and determining task states for PlanFlow tasks."""

    def is_due(self, occurrence: TaskOccurrence, now: datetime) -> bool:
        """Return True if the task is currently due.

        Args:
            occurrence: The TaskOccurrence to check.
            now: The current datetime.

        Returns:
            True if the occurrence is due (now >= scheduled_for), else False.

        Constraints:
            Pure, deterministic, no side effects.
        """
        return now >= occurrence.scheduled_for

    def is_missed(self, occurrence: TaskOccurrence, now: datetime) -> bool:
        """Return True if scheduled time has passed and not marked done.

        Args:
            occurrence: The TaskOccurrence to check.
            now: The current datetime.

        Returns:
            True if the occurrence is missed (now > scheduled_for), else False.

        Constraints:
            Pure, deterministic, no side effects.
        """
        return now > occurrence.scheduled_for

    def should_retry(self, execution: TaskExecution) -> bool:
        """Check if task is eligible for retry based on RetryPolicy.

        Args:
            execution: The TaskExecution to check.

        Returns:
            True if retries remain and state is missed or pending, else False.

        Constraints:
            Pure, deterministic, no side effects.
        """
        return execution.is_reschedulable

    def get_next_occurrence(
        self,
        task: TaskDefinition,
        from_time: datetime,
        calendar: CalendarPlanner,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        slot_pool: list[TimeSlot],
        max_per_day: int
    ) -> TaskOccurrence | None:
        """Generate the next occurrence for this task, supporting pinned time and recurrence.

        If the task includes a valid `pinned_time`, return an occurrence for that time
        (if it passes calendar validation). If the pinned time is invalid or missing,
        use recurrence rules and calendar logic to select the next slot, searching day by day until a slot is found.
        For high priority tasks, always select the earliest available slot.

        Args:
            task: The TaskDefinition to schedule.
            from_time: The datetime to start searching from.
            calendar: CalendarPlanner for conflict detection.
            scheduled_occurrences: List of already scheduled TaskOccurrence.
            working_hours: List of WorkingHours for user availability.
            slot_pool: List of preferred TimeSlots.
            max_per_day: Max task occurrences per calendar day.

        Returns:
            A new TaskOccurrence if scheduling is possible, else None.

        Constraints:
            - No mutation of inputs.
            - Must honor per-day caps, user time slots, and working hours.
            - Return None if scheduling isn't possible.
            - Prioritize preferred time slots and high priority tasks.
            - Pinned time takes precedence if valid.
        """
        # 1. Pinned time logic
        pinned_time = getattr(task, "pinned_time", None)
        if pinned_time is not None:
            if calendar.is_pinned_time_valid(pinned_time, scheduled_occurrences, working_hours, max_per_day):
                return TaskOccurrence(
                    id=f"{task.id}:pinned:{int(pinned_time.timestamp())}",
                    task_id=task.id,
                    scheduled_for=pinned_time,
                    slot_name=None,
                    pinned_time=pinned_time,
                )
            else:
                return None
        # 2. Recurrence logic: search day by day for next available preferred slot
        if not task.recurrence:
            return None
        search_date = (from_time + task.recurrence).date()
        # Try up to 30 days ahead to avoid infinite loop
        for day_offset in range(0, 30):
            candidate_date = search_date + timedelta(days=day_offset)
            weekday = candidate_date.strftime("%A").lower()
            wh_for_day = [wh for wh in working_hours if wh.day == weekday]
            if not wh_for_day:
                continue
            allowed_slot_names: set[str] = set()
            for wh in wh_for_day:
                allowed_slot_names.update(wh.allowed_slots)
            preferred_slots = [s for s in slot_pool if s.name in getattr(task, "preferred_slots", []) and s.name in allowed_slot_names]
            other_slots = [s for s in slot_pool if s.name not in getattr(task, "preferred_slots", []) and s.name in allowed_slot_names]
            slots_to_try = preferred_slots + other_slots
            if task.priority == "high":
                slots_to_try = sorted(slots_to_try, key=lambda s: s.start)
            # For each slot, skip if already occupied for that day
            for slot in slots_to_try:
                slot_dt = datetime.combine(candidate_date, slot.start)
                if slot_dt <= from_time:
                    continue
                if not (slot.start <= slot_dt.time() <= slot.end):
                    continue
                # Check if slot is already occupied for this day and slot
                slot_occupied = any(
                    occ.scheduled_for.date() == candidate_date and occ.slot_name == slot.name
                    for occ in scheduled_occurrences
                )
                if slot_occupied:
                    continue
                if not calendar.is_slot_available(slot_dt, scheduled_occurrences, working_hours, max_per_day, slot_pool=slot_pool):
                    continue
                return TaskOccurrence(
                    id=f"{task.id}:{int(slot_dt.timestamp())}",
                    task_id=task.id,
                    scheduled_for=slot_dt,
                    slot_name=slot.name,
                    pinned_time=None,
                )
        return None

    def reschedule_retry(
        self,
        occurrence: TaskOccurrence,
        policy: RetryPolicy,
        now: datetime,
        calendar: CalendarPlanner,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        slot_pool: list[TimeSlot],
        max_per_day: int,
        retries_remaining: int | None = None
    ) -> TaskOccurrence | None:
        """Generate a retry occurrence based on retry policy and availability.

        Args:
            occurrence: The TaskOccurrence to retry.
            policy: The RetryPolicy to use.
            now: The current datetime.
            calendar: CalendarPlanner for conflict detection.
            scheduled_occurrences: All current task occurrences.
            working_hours: List of WorkingHours for user availability.
            slot_pool: List of preferred TimeSlots.
            max_per_day: Max task occurrences per calendar day.
            retries_remaining: Number of retries left (enforced if provided).

        Returns:
            A new TaskOccurrence if retry is possible, else None.

        Constraints:
            - No mutation of inputs.
            - Must honor per-day caps, user time slots, and working hours.
            - Return None if scheduling isn't possible.
            - Prioritize preferred time slots and high priority tasks.
        """
        # Enforce retry limit: do not schedule if max_retries is 0 or already reached
        if policy.max_retries == 0:
            return None
        if retries_remaining is not None and retries_remaining <= 0:
            return None
        retry_interval = getattr(policy, "retry_interval", timedelta(hours=1))
        base_time = now + retry_interval
        # Try up to 7 days ahead to find a valid slot
        for day_offset in range(0, 7):
            candidate_date = (base_time + timedelta(days=day_offset)).date()
            weekday = candidate_date.strftime("%A").lower()
            wh_for_day = [wh for wh in working_hours if wh.day == weekday]
            if not wh_for_day:
                continue
            allowed_slot_names: set[str] = set()
            for wh in wh_for_day:
                allowed_slot_names.update(wh.allowed_slots)
            # Try to retry in the same slot as before, if possible
            preferred_slots = [s for s in slot_pool if s.name in allowed_slot_names and (occurrence.slot_name is None or s.name == occurrence.slot_name)]
            if not preferred_slots:
                preferred_slots = [s for s in slot_pool if s.name in allowed_slot_names]
            preferred_slots = sorted(preferred_slots, key=lambda s: s.start)
            for slot in preferred_slots:
                slot_dt = datetime.combine(candidate_date, slot.start)
                if slot_dt < base_time:
                    continue
                if not (slot.start <= slot_dt.time() <= slot.end):
                    continue
                if not calendar.is_slot_available(slot_dt, scheduled_occurrences, working_hours, max_per_day, slot_pool=slot_pool):
                    continue
                return TaskOccurrence(
                    id=f"{occurrence.task_id}:retry:{int(slot_dt.timestamp())}",
                    task_id=occurrence.task_id,
                    scheduled_for=slot_dt,
                    slot_name=slot.name,
                    pinned_time=None,
                )
        # If no slot found in allowed working hours, do not schedule a retry
        return None
