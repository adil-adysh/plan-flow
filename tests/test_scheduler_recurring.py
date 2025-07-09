
"""
Tests for recurring task logic in Scheduler.

- Verifies that a recurring task executes multiple times and triggers callback and speech.
- Ensures rescheduled time is persisted to store after execution.
"""


import time
from datetime import datetime, timedelta
from collections.abc import Callable
from pathlib import Path
import pytest

from addon.globalPlugins.planflow.task.schedule import Scheduler
from addon.globalPlugins.planflow.task.model import ScheduledTask
from addon.globalPlugins.planflow.task.store import TaskStore
from tests.utils.dummies import DummySpeech, DummyCallback



def make_task(
    label: str,
    due: datetime,
    recurrence: timedelta | None = None,
    callback: Callable[[], None] | None = None
) -> ScheduledTask:
    """Create a ScheduledTask with optional recurrence and callback.

    Args:
        label: Task label.
        due: Due datetime for the task.
        recurrence: Optional recurrence interval.
        callback: Optional callback function.

    Returns:
        ScheduledTask: The constructed task.
    """
    task = ScheduledTask(label=label, time=due, recurrence=recurrence)
    if callback:
        task.callback = callback
    return task

@pytest.fixture
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
    """Test that a recurring task executes multiple times and triggers callback and speech.

    Args:
        speech: DummySpeech instance for capturing reminders.
        callback: DummyCallback instance for tracking callback invocations.
        store: TaskStore instance for task persistence.
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
    reminders = [m for m in speech.messages if "Reminder: Recurring" in m]
    assert len(reminders) >= 2, "Recurring reminder did not occur multiple times"
    assert callback.called, "Callback for recurring task not triggered"




def test_task_reschedule_after_recurrence_persists_in_store(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """Test that a recurring task's rescheduled time is persisted in the store after execution.

    Args:
        speech: DummySpeech instance for capturing reminders.
        callback: DummyCallback instance for tracking callback invocations.
        store: TaskStore instance for task persistence.
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
    updated = next((t for t in store.tasks if t.label == "PersistentRecurring"), None)
    assert updated is not None, "Recurring task missing from store after execution"
    assert updated.time > due, "Recurring task time not updated after run"
