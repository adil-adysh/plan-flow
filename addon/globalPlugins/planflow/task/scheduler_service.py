
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
        """Generate the next recurrence occurrence for this task.

        Args:
            task: The TaskDefinition to schedule.
            from_time: The datetime to calculate from.
            calendar: CalendarPlanner for conflict detection.
            scheduled_occurrences: All current task occurrences.
            working_hours: List of WorkingHours for user availability.
            slot_pool: List of preferred TimeSlots.
            max_per_day: Max task occurrences per calendar day.

        Returns:
            A new TaskOccurrence if recurrence is possible, else None.

        Constraints:
            - No mutation of inputs.
            - Must honor per-day caps, user time slots, and working hours.
            - Return None if scheduling isn't possible.
            - Prioritize preferred time slots and high priority tasks.
        """
        if not task.recurrence or not isinstance(task.recurrence, timedelta):
            return None
        base_time = from_time + task.recurrence
        weekday = base_time.strftime("%A").lower()
        wh_for_day: list[WorkingHours] = [wh for wh in working_hours if wh.day == weekday]
        if not wh_for_day:
            return None
        allowed_slot_names: set[str] = set()
        for wh in wh_for_day:
            allowed_slot_names.update(wh.allowed_slots)
        preferred_slots = [s for s in slot_pool if s.name in allowed_slot_names and s.name in task.preferred_slots]
        if not preferred_slots:
            preferred_slots = [s for s in slot_pool if s.name in allowed_slot_names]
        preferred_slots.sort(key=lambda s: s.start)
        for slot in preferred_slots:
            slot_dt = base_time.replace(hour=slot.start.hour, minute=slot.start.minute, second=0, microsecond=0)
            if not (slot.start <= slot_dt.time() <= slot.end):
                continue
            if not calendar.is_slot_available(slot_dt, scheduled_occurrences, working_hours, max_per_day):
                continue
            return TaskOccurrence(
                id=f"{task.id}:{int(slot_dt.timestamp())}",
                task_id=task.id,
                scheduled_for=slot_dt,
                slot_name=slot.name,
            )
        next_slot = calendar.next_available_slot(
            after=base_time,
            slot_pool=slot_pool,
            scheduled_occurrences=scheduled_occurrences,
            working_hours=working_hours,
            max_per_day=max_per_day
        )
        if not next_slot:
            return None
        # Find the slot name for the returned datetime
        slot_name = None
        for slot in slot_pool:
            if slot.start == next_slot.time():
                slot_name = slot.name
                break
        return TaskOccurrence(
            id=f"{task.id}:{int(next_slot.timestamp())}",
            task_id=task.id,
            scheduled_for=next_slot,
            slot_name=slot_name,
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
        max_per_day: int
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

        Returns:
            A new TaskOccurrence if retry is possible, else None.

        Constraints:
            - No mutation of inputs.
            - Must honor per-day caps, user time slots, and working hours.
            - Return None if scheduling isn't possible.
            - Prioritize preferred time slots and high priority tasks.
        """
        # For retry, schedule at now + retry interval (assume 1 hour if not specified)
        retry_interval = getattr(policy, "retry_interval", timedelta(hours=1))
        if not isinstance(retry_interval, timedelta):
            retry_interval = timedelta(hours=1)
        base_time = now + retry_interval
        weekday = base_time.strftime("%A").lower()
        wh_for_day: list[WorkingHours] = [wh for wh in working_hours if wh.day == weekday]
        if not wh_for_day:
            return None
        allowed_slot_names: set[str] = set()
        for wh in wh_for_day:
            allowed_slot_names.update(wh.allowed_slots)
        preferred_slots = [s for s in slot_pool if s.name in allowed_slot_names and (occurrence.slot_name is None or s.name == occurrence.slot_name)]
        if not preferred_slots:
            preferred_slots = [s for s in slot_pool if s.name in allowed_slot_names]
        preferred_slots.sort(key=lambda s: s.start)
        for slot in preferred_slots:
            slot_dt = base_time.replace(hour=slot.start.hour, minute=slot.start.minute, second=0, microsecond=0)
            if not (slot.start <= slot_dt.time() <= slot.end):
                continue
            if not calendar.is_slot_available(slot_dt, scheduled_occurrences, working_hours, max_per_day):
                continue
            return TaskOccurrence(
                id=f"{occurrence.task_id}:retry:{int(slot_dt.timestamp())}",
                task_id=occurrence.task_id,
                scheduled_for=slot_dt,
                slot_name=slot.name,
            )
        next_slot = calendar.next_available_slot(
            after=base_time,
            slot_pool=slot_pool,
            scheduled_occurrences=scheduled_occurrences,
            working_hours=working_hours,
            max_per_day=max_per_day
        )
        if not next_slot:
            return None
        # Find the slot name for the returned datetime
        slot_name = None
        for slot in slot_pool:
            if slot.start == next_slot.time():
                slot_name = slot.name
                break
        return TaskOccurrence(
            id=f"{occurrence.task_id}:retry:{int(next_slot.timestamp())}",
            task_id=occurrence.task_id,
            scheduled_for=next_slot,
            slot_name=slot_name,
        )
        return None
