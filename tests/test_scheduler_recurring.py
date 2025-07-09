"""
Tests for recurring task logic in Scheduler:
- Task recurs and executes multiple times
- Rescheduled time is persisted to store
"""

import time
from datetime import datetime, timedelta
import pytest
from addon.globalPlugins.planflow.task.schedule import Scheduler
from addon.globalPlugins.planflow.task.model import ScheduledTask
from addon.globalPlugins.planflow.task.store import TaskStore
from collections.abc import Callable
from pathlib import Path

from tests.utils.dummies import DummySpeech, DummyCallback



def make_task(
    label: str,
    due: datetime,
    recurrence: timedelta | None = None,
    callback: Callable[[], None] | None = None
) -> ScheduledTask:
    """
    Helper to create a ScheduledTask with optional recurrence and callback.
    """
    task = ScheduledTask(label=label, time=due, recurrence=recurrence)
    if callback:
        task.callback = callback
    return task
def db_path(tmp_path: Path) -> Path:
    """Fixture providing a temporary path for the test database file."""
    return tmp_path / "db.json"



@pytest.fixture
def store(db_path: Path) -> TaskStore:
    """Fixture providing a TaskStore using a temporary database file."""
    return TaskStore(file_path=str(db_path))



def test_recurring_task_runs_multiple_times(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Test that a recurring task executes multiple times and triggers callback and speech.
    """
    due = datetime.now() + timedelta(seconds=1)
    recur = timedelta(seconds=1)
    task = make_task("Recurring", due, recurrence=recur, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(3)
    sched.stop()
    # Check that the recurring reminder occurred multiple times
    reminders = [m for m in speech.messages if "Reminder: Recurring" in m]
    assert len(reminders) >= 2, "Recurring reminder did not occur multiple times"
    # Check that the callback for the recurring task was triggered
    assert callback.called, "Callback for recurring task not triggered"



def test_task_reschedule_after_recurrence_persists_in_store(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Test that a recurring task's rescheduled time is persisted in the store after execution.
    """
    recur = timedelta(seconds=1)
    due = datetime.now() + timedelta(seconds=1)
    task = make_task("PersistentRecurring", due, recurrence=recur, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(3)
    sched.stop()
    # Check that the recurring task is still in the store after execution
    updated = next((t for t in store.tasks if t.label == "PersistentRecurring"), None)
    assert updated is not None, "Recurring task missing from store after execution"
    # Check that the recurring task's time was updated after run
    assert updated.time > due, "Recurring task time not updated after run"
