"""SmartSchedulerService: Real-time orchestrator for PlanFlow task execution.

Coordinates timers, detects missed executions, performs safe retries and recurrences, and enforces all task and slot constraints.
"""

from __future__ import annotations
import threading
from datetime import datetime
from collections.abc import Callable
from .task_model import TaskOccurrence, TaskExecution
from .execution_repository import ExecutionRepository
from .scheduler_service import TaskScheduler
from .calendar_planner import CalendarPlanner
from .recovery_service import RecoveryService

_RECOVERY_GRACE_SECONDS: int = 30


class SmartSchedulerService:
    """Real-time scheduling orchestrator for PlanFlow.

    Triggers TaskOccurrences at their scheduled time, prevents re-execution, delegates retry/recurrence,
    enforces constraints, and recovers missed tasks.
    """

    def __init__(
        self,
        execution_repo: ExecutionRepository,
        scheduler: TaskScheduler,
        calendar: CalendarPlanner,
        recovery: RecoveryService,
        now_fn: Callable[[], datetime] = datetime.now
    ) -> None:
        """Initialize SmartSchedulerService.

        Args:
            execution_repo: Persistent backend for occurrences and execution history.
            scheduler: Core task recurrence/retry logic.
            calendar: Enforces working hours, slot validation, and caps.
            recovery: Handles missed tasks rescheduling.
            now_fn: Injectible clock for testability.
        """
        self._execution_repo = execution_repo
        self._scheduler = scheduler
        self._calendar = calendar
        self._recovery = recovery
        self._now_fn = now_fn
        self._timers: dict[str, threading.Timer] = {}
        self._paused: bool = False
        self._lock: threading.RLock = threading.RLock()

    def start(self) -> None:
        """Start the scheduler: resumes scheduling and checks for missed tasks."""
        with self._lock:
            self._paused = False
            self._cancel_all_timers()
            self.schedule_all()
            self.check_for_missed_tasks()

    def pause(self) -> None:
        """Pause the scheduler: cancels all timers and prevents future scheduling."""
        with self._lock:
            self._paused = True
            self._cancel_all_timers()

    def schedule_all(self) -> None:
        """Schedule all future TaskOccurrences that are not yet executed."""
        with self._lock:
            self._cancel_all_timers()
            if self._paused:
                return
            occurrences = self._execution_repo.list_occurrences()
            executed_ids = {e.occurrence_id for e in self._execution_repo.list_executions() if e.state == "done"}
            now = self._now_fn()
            for occ in occurrences:
                if occ.scheduled_for > now and occ.id not in executed_ids:
                    self.schedule_occurrence(occ)

    def schedule_occurrence(self, occ: TaskOccurrence) -> None:
        """Schedule a single TaskOccurrence if valid and not already executed."""
        with self._lock:
            if self._paused:
                return
            scheduled = self._execution_repo.list_occurrences()
            executed_ids = {e.occurrence_id for e in self._execution_repo.list_executions() if e.state == "done"}
            if occ.id in executed_ids:
                return
            calendar_config = self._calendar.get_config()
            if not self._calendar.is_slot_available(
                occ.scheduled_for,
                scheduled,
                calendar_config.working_hours,
                calendar_config.max_per_day,
                calendar_config.slot_pool,
            ):
                return
            if occ.id in self._timers:
                self._timers[occ.id].cancel()
                del self._timers[occ.id]
            delay = (occ.scheduled_for - self._now_fn()).total_seconds()
            if delay <= 0:
                self._on_trigger(occ)
            else:
                timer = threading.Timer(delay, self._on_trigger, args=(occ,))
                timer.daemon = True
                self._timers[occ.id] = timer
                timer.start()

    def check_for_missed_tasks(self) -> None:
        """Check for missed TaskOccurrences and trigger or recover as needed."""
        with self._lock:
            if self._paused:
                return
            occurrences = self._execution_repo.list_occurrences()
            executed_ids = {e.occurrence_id for e in self._execution_repo.list_executions() if e.state == "done"}
            now = self._now_fn()
            for occ in occurrences:
                if occ.id in executed_ids:
                    continue
                delta = (now - occ.scheduled_for).total_seconds()
                if 0 < delta <= _RECOVERY_GRACE_SECONDS:
                    self._on_trigger(occ)
                elif delta > _RECOVERY_GRACE_SECONDS:
                    self._trigger_recovery(occ)

    def _on_trigger(self, occ: TaskOccurrence) -> None:
        """Handle the execution of a TaskOccurrence: mark as done, handle retry/recurrence."""
        with self._lock:
            if occ.id in self._timers:
                self._timers[occ.id].cancel()
                del self._timers[occ.id]
            exec = TaskExecution(
                occurrence_id=occ.id,
                state="done",
                retries_remaining=0,
                history=[],
            )
            self._execution_repo.add_execution(exec)
            task = self._execution_repo.get_task(occ.task_id)
            if task is not None:
                scheduled = self._execution_repo.list_occurrences()
                calendar_config = self._calendar.get_config()
                retry_occ = self._scheduler.reschedule_retry(
                    occ,
                    task.retry_policy,
                    self._now_fn(),
                    self._calendar,
                    scheduled,
                    calendar_config.working_hours,
                    calendar_config.slot_pool,
                    calendar_config.max_per_day,
                )
                if retry_occ is not None:
                    self.schedule_occurrence(retry_occ)
                    return
                if task.recurrence is not None:
                    next_occ = self._scheduler.get_next_occurrence(
                        task,
                        self._now_fn(),
                        self._calendar,
                        scheduled,
                        calendar_config.working_hours,
                        calendar_config.slot_pool,
                        calendar_config.max_per_day,
                    )
                    if next_occ is not None:
                        self.schedule_occurrence(next_occ)

    def _trigger_recovery(self, occ: TaskOccurrence) -> None:
        """Delegate missed occurrence to RecoveryService for rescheduling."""
        all_executions = self._execution_repo.list_executions()
        all_occurrences = {o.id: o for o in self._execution_repo.list_occurrences()}
        all_tasks = {t.id: t for t in self._execution_repo.list_tasks()}
        calendar_config = self._calendar.get_config()
        new_occs = self._recovery.recover_missed_occurrences(
            executions=all_executions,
            occurrences=all_occurrences,
            tasks=all_tasks,
            now=self._now_fn(),
            calendar=self._calendar,
            scheduled_occurrences=list(all_occurrences.values()),
            working_hours=calendar_config.working_hours,
            slot_pool=calendar_config.slot_pool,
            max_per_day=calendar_config.max_per_day,
        )
        for o in new_occs:
            self.schedule_occurrence(o)

    def _cancel_all_timers(self) -> None:
        """Cancel all active timers and clear the timer dictionary."""
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()
