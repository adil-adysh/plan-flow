"""Task scheduling logic for PlanFlow NVDA add-on.

This module implements the TaskScheduler class, which encapsulates core scheduling, recurrence, and retry logic for tasks. All logic is pure, testable, and NVDA-independent.
"""

from __future__ import annotations
from datetime import datetime
from .task_model import TaskDefinition, TaskOccurrence, TaskExecution, RetryPolicy

class TaskScheduler:
    """Encapsulates scheduling, recurrence, and retry logic for PlanFlow tasks."""

    def is_due(self, occurrence: TaskOccurrence, now: datetime) -> bool:
        """Check if a task occurrence is currently due.

        Args:
            occurrence: The TaskOccurrence to check.
            now: The current datetime.

        Returns:
            True if the occurrence is due (now >= scheduled_for), else False.
        """
        return now >= occurrence.scheduled_for

    def is_missed(self, occurrence: TaskOccurrence, now: datetime) -> bool:
        """Determine if an occurrence has passed and was not marked complete.

        Args:
            occurrence: The TaskOccurrence to check.
            now: The current datetime.

        Returns:
            True if the occurrence is missed (now > scheduled_for), else False.
        """
        return now > occurrence.scheduled_for

    def get_next_occurrence(self, task: TaskDefinition, from_time: datetime) -> TaskOccurrence | None:
        """Return the next scheduled occurrence based on recurrence, or None.

        Args:
            task: The TaskDefinition to schedule.
            from_time: The datetime to calculate from.

        Returns:
            A new TaskOccurrence if recurrence is set, else None.
        """
        if task.recurrence is None:
            return None
        next_time = from_time + task.recurrence
        return TaskOccurrence(
            id=f"{task.id}:{int(next_time.timestamp())}",
            task_id=task.id,
            scheduled_for=next_time,
        )

    def should_retry(self, execution: TaskExecution) -> bool:
        """Return True if the task should be retried, based on retry policy.

        Args:
            execution: The TaskExecution to check.

        Returns:
            True if retries remain and state is missed or pending, else False.
        """
        return execution.is_reschedulable

    def reschedule_retry(self, occurrence: TaskOccurrence, policy: RetryPolicy, now: datetime) -> TaskOccurrence:
        """Return a new occurrence based on retry_interval from now.

        Args:
            occurrence: The TaskOccurrence to retry.
            policy: The RetryPolicy to use.
            now: The current datetime.

        Returns:
            A new TaskOccurrence scheduled for now + retry_interval.
        """
        new_time = now + policy.retry_interval
        return TaskOccurrence(
            id=f"{occurrence.task_id}:retry:{int(new_time.timestamp())}",
            task_id=occurrence.task_id,
            scheduled_for=new_time,
        )
