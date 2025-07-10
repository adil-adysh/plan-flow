"""Recovery service for PlanFlow: detects and recovers missed or overdue task executions.

Implements logic to analyze missed tasks and suggest next steps, including retries and recurrences.
"""

from __future__ import annotations
from datetime import datetime
 
from .task_model import TaskExecution, TaskOccurrence, TaskDefinition
from .scheduler_service import TaskScheduler

class RecoveryService:
    """Encapsulates logic for analyzing missed tasks and suggesting next steps.
    """



    def recover_missed_occurrences(
        self,
        executions: list[TaskExecution],
        occurrences: dict[str, TaskOccurrence],
        tasks: dict[str, TaskDefinition],
        now: datetime,
    ) -> list[TaskOccurrence]:
        """Recover retry or recurrence for missed tasks.

        Args:
            executions: All known executions (including missed).
            occurrences: Dict of occurrence_id → TaskOccurrence.
            tasks: Dict of task_id → TaskDefinition.
            now: Logical clock (no real-time reading).

        Returns:
            A list of new TaskOccurrences that should be scheduled next (unsaved).
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
            task = tasks.get(occ.task_id)
            if task is None:
                continue
            # Retry logic
            if scheduler.should_retry(execution) and execution.retries_remaining > 0:
                retry_occ = scheduler.reschedule_retry(occ, task.retry_policy, now)
                new_occurrences.append(retry_occ)
                continue
            # Recurrence logic
            if task.recurrence is not None:
                next_occ = scheduler.get_next_occurrence(task, occ.scheduled_for)
                if next_occ is not None and next_occ.scheduled_for > now:
                    new_occurrences.append(next_occ)
        return new_occurrences
