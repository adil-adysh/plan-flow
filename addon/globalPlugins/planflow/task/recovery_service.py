
"""Recovery service for PlanFlow: detects and recovers missed or overdue task executions.

Implements logic to analyze missed tasks and suggest next steps, including retries and recurrences.
"""

from __future__ import annotations
from datetime import datetime
from .task_model import TaskExecution, TaskOccurrence, TaskDefinition, WorkingHours, TimeSlot
from .scheduler_service import TaskScheduler
from .calendar_planner import CalendarPlanner

class RecoveryService:
    """Encapsulates logic for analyzing missed tasks and generating next valid occurrences.

    This service recovers missed or pending task executions, respecting recurrence, retry policy, working hours, slot pool, and per-day caps. Pinned-time occurrences are excluded from recovery logic.
    """

    def recover_missed_occurrences(
        self,
        executions: list[TaskExecution],
        occurrences: dict[str, TaskOccurrence],
        tasks: dict[str, TaskDefinition],
        now: datetime,
        calendar: CalendarPlanner,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        slot_pool: list[TimeSlot],
        max_per_day: int
    ) -> list[TaskOccurrence]:
        """Return new retry or recurrence occurrences for missed tasks.

        Args:
            executions: All known execution records.
            occurrences: Dict of occurrence_id → TaskOccurrence.
            tasks: Dict of task_id → TaskDefinition.
            now: Logical current time.
            calendar: CalendarPlanner for availability checks.
            scheduled_occurrences: List of already scheduled TaskOccurrence.
            working_hours: Active time spans for each weekday.
            slot_pool: User-preferred time slots.
            max_per_day: Allowed task count per day.

        Returns:
            List of new TaskOccurrences (unsaved) ready to be scheduled. Inputs are unmodified.

        Notes:
            Occurrences with pinned_time are treated as user-fixed and excluded from recovery retry/reschedule logic.
        """
        scheduler = TaskScheduler()
        new_occurrences: list[TaskOccurrence] = []
        for execution in executions:
            # Only recover missed or pending tasks scheduled before now
            if execution.state not in ("missed", "pending"):
                continue
            occ = occurrences.get(execution.occurrence_id)
            if occ is None or occ.scheduled_for >= now:
                continue
            # Skip pinned-time occurrences
            if occ.pinned_time is not None:
                continue
            task = tasks.get(occ.task_id)
            if task is None:
                continue
            # Only one of retry or recurrence per missed occurrence
            scheduled = False
            # Retry logic
            if scheduler.should_retry(execution) and execution.retries_remaining > 0:
                retry_occ = scheduler.reschedule_retry(
                    occ,
                    task.retry_policy,
                    now,
                    calendar,
                    scheduled_occurrences,
                    working_hours,
                    slot_pool,
                    max_per_day
                )
                if retry_occ is not None:
                    new_occurrences.append(retry_occ)
                    scheduled = True
            # Recurrence logic (only if not retried)
            if not scheduled and task.recurrence is not None:
                next_occ = scheduler.get_next_occurrence(
                    task,
                    occ.scheduled_for,
                    calendar,
                    scheduled_occurrences,
                    working_hours,
                    slot_pool,
                    max_per_day
                )
                if next_occ is not None and next_occ.scheduled_for > now:
                    new_occurrences.append(next_occ)
        return new_occurrences
