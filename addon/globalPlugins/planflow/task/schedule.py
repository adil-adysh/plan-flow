
"""
Task scheduling and execution logic for PlanFlow.
Uses APScheduler for reliable, multi-threaded scheduling.
Handles recurrence, missed tasks, and accessibility speech callbacks.
"""


from __future__ import annotations
from datetime import datetime
from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

from .model import ScheduledTask
from .store import TaskStore


class Scheduler:

    def start(self) -> None:
        """
        Start the background scheduler.
        """
        if not self._started:
            self._scheduler.start()
            self._started = True
    """
    Schedules and executes tasks using APScheduler.
    Reschedules recurring tasks, handles missed tasks on boot,
    and invokes a speech callback for accessibility.
    """


    def __init__(
        self,
        store: TaskStore | None = None,
        speech_callback: Callable[[str], None] | None = None
    ) -> None:
        """
        Initialize the Scheduler with optional TaskStore and speech callback.

        Args:
            store: Optional TaskStore instance for persistence.
            speech_callback: Optional callable for accessibility speech output.
        """
        super().__init__()
        self.store: TaskStore = store or TaskStore()
        self.speech_callback: Callable[[str], None] = speech_callback or (lambda msg: None)
        self._scheduler: BackgroundScheduler = BackgroundScheduler(
            executors={'default': ThreadPoolExecutor(5)},
            job_defaults={'misfire_grace_time': 30}
        )
        self._started: bool = False


    @property
    def is_running(self) -> bool:
        """Return True if the underlying APScheduler is running."""
        return self._scheduler.running

    def stop(self) -> None:
        """
        Stop the background scheduler.
        """
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False

    def schedule_all(self) -> None:
        """
        Schedule all tasks from the store.
        Handles missed tasks and reschedules recurring ones.
        """
        now = datetime.now()
        for task in self.store.tasks:
            if task.is_due(now):
                self.speech_callback(f"You missed a task: {task.label}. Rescheduling it.")
                self._handle_missed(task)
            else:
                self._schedule_task(task)

    def _schedule_task(self, task: ScheduledTask) -> None:
        """
        Schedule a single task using APScheduler with safe error handling.
        Handles recurrence.
        """
        def run_task() -> None:
            self.speech_callback(f"Reminder: {task.label}")
            if task.callback:
                try:
                    task.callback()
                except Exception:
                    pass
            if task.recurrence:
                task.time += task.recurrence
                self.store.update(task)
                self._schedule_task(task)

        _: object = self._scheduler.add_job(
            func=run_task,
            trigger=DateTrigger(run_date=task.time),
            id=task.id,
            replace_existing=True,
            misfire_grace_time=30  # allow grace period for near-past tasks
        )

    def _handle_missed(self, task: ScheduledTask) -> None:
        """
        Handle missed tasks gracefully.
        For recurring tasks, replay missed reminders and reschedule.
        For non-recurring tasks, notify and remove.
        """
        now = datetime.now()
        if task.recurrence:
            while task.time < now:
                self.speech_callback(f"Reminder: {task.label}")
                if task.callback:
                    try:
                        task.callback()
                    except Exception:
                        pass
                task.time += task.recurrence
            self.store.update(task)
            self._schedule_task(task)
        else:
            self.speech_callback(f"Task '{task.label}' was missed and will not recur.")
            self.store.remove(task.id)
