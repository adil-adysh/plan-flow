
"""
Task scheduling and execution logic for PlanFlow.
Uses the `schedule` library to run and reschedule tasks.
Integrates with TaskStore and supports accessibility via a speech callback.
No NVDA-specific APIs are used; all code is standard Python 3.11+.
"""

from __future__ import annotations
import threading
import time
from datetime import datetime
from collections.abc import Callable
import schedule
from .store import TaskStore
from .model import ScheduledTask


class Scheduler:
    """
    Handles scheduling and execution of tasks using the `schedule` library.
    Automatically reschedules missed tasks based on recurrence settings.
    Accessible notifications are provided via a user-supplied speech callback.
    """

    def __init__(self, store: TaskStore | None = None, speech_callback: Callable[[str], None] | None = None):  # noqa: D107
        """
        Initialize the Scheduler.
        - store: Optional TaskStore instance. If not provided, a new one is created.
        - speech_callback: Optional callable for accessibility notifications (e.g., text-to-speech).
        """
        self.store = store or TaskStore()
        self.speech_callback: Callable[[str], None] = speech_callback or (lambda msg: None)
        self._stop = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """
        Start the scheduler loop in a background thread.
        """
        if self._thread and self._thread.is_alive():
            return
        self._stop = False
        self._thread = threading.Thread(target=self._run_scheduler_loop, daemon=True)
        self._thread.start()

    def _run_scheduler_loop(self) -> None:
        while not self._stop:
            schedule.run_pending()
            time.sleep(1)
        self._thread = None

    def stop(self) -> None:
        """
        Stop the scheduler loop and wait for the thread to finish.
        """
        self._stop = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def schedule_all(self) -> None:
        """
        Schedules all tasks from the store, handling missed tasks gracefully.
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
        Internal function to schedule a task using `schedule`.
        If the task is due now or in the past, schedule it to run immediately in the scheduler thread.
        """
        now = datetime.now()
        delay = int((task.time - now).total_seconds())

        def run():
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

        if delay <= 0:
            # Schedule to run as soon as possible in the scheduler thread
            _ = schedule.every(1).seconds.do(run).tag(task.id)  # type: ignore
            # Mark the job as ready to run immediately
            job = schedule.get_jobs(tag=task.id)[-1]
            job.last_run = None
            job.next_run = now
        else:
            _ = schedule.every(delay).seconds.do(run).tag(task.id)  # type: ignore

    def _handle_missed(self, task: ScheduledTask) -> None:
        """
        Handles rescheduling of a missed task.
        If it is non-repeating, notify and remove.
        If it recurs, execute callback for each missed interval and reschedule for the next valid time.
        """
        now = datetime.now()
        if task.recurrence:
            # Execute callback for each missed interval
            missed_count = 0
            while task.time < now:
                self.speech_callback(f"Reminder: {task.label}")
                if task.callback:
                    try:
                        task.callback()
                    except Exception:
                        pass  # Don't crash scheduler on callback error
                task.time += task.recurrence
                missed_count += 1
            self.store.update(task)
            self._schedule_task(task)
        else:
            self.speech_callback(f"Task '{task.label}' was missed and will not recur.")
            self.store.remove(task.id)
