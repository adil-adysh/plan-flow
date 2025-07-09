"""
Tests for missed task handling in Scheduler:
- Non-recurring missed tasks are removed
- Recurring missed tasks are rescheduled forward
"""

import time
from datetime import datetime, timedelta
import pytest
from addon.globalPlugins.planflow.task.schedule import Scheduler
from addon.globalPlugins.planflow.task.model import ScheduledTask
from addon.globalPlugins.planflow.task.store import TaskStore
from collections.abc import Callable

from tests.utils.dummies import DummySpeech, DummyCallback


@pytest.fixture
def speech() -> DummySpeech:
    """Fixture providing a dummy speech callback."""
    return DummySpeech()


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




@pytest.fixture
def callback() -> DummyCallback:
    """Fixture providing a dummy callback."""
    return DummyCallback()



from pathlib import Path

@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Fixture providing a temporary path for the test database file."""
    return tmp_path / "db.json"



@pytest.fixture
def store(db_path: Path) -> TaskStore:
    """Fixture providing a TaskStore using a temporary database file."""
    return TaskStore(file_path=str(db_path))



def test_missed_task(
    speech: DummySpeech, store: TaskStore
) -> None:
    """
    Test that a non-recurring missed task is reported and removed from the store.
    """
    due = datetime.now() - timedelta(seconds=5)
    task = make_task("Missed Task", due)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    # Check that the missed task was reported
    assert any("missed a task" in m for m in speech.messages), "Missed task not reported"
    # Check that the non-recurring task removal was reported
    assert any("will not recur" in m for m in speech.messages), "Non-recurring task removal not reported"
    # Check that the missed one-time task was removed from the store
    assert not any(t.label == "Missed Task" for t in store.tasks), "Missed one-time task not removed"



def test_missed_recurring_task_reschedules_correctly(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Test that a missed recurring task is rescheduled and its callback is called.
    """
    due = datetime.now() - timedelta(seconds=3)
    task = make_task("MissedRecurring", due, recurrence=timedelta(seconds=2), callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(3)
    sched.stop()
    # Check that the callback was called for the missed recurring task
    assert callback.called, "Missed recurring task callback not called"
    # Check that the reminder message was spoken for the missed recurring task
    assert any("Reminder: MissedRecurring" in m for m in speech.messages), "Reminder message missing for missed recurring task"



def test_scheduler_gracefully_handles_past_task_without_callback(
    speech: DummySpeech, store: TaskStore
) -> None:
    """
    Test that the scheduler gracefully handles a missed one-time task without a callback.
    """
    due = datetime.now() - timedelta(minutes=1)
    task = make_task("GracefulMiss", due)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    # Check that the missed task speech was triggered
    assert any("GracefulMiss" in m for m in speech.messages), "Missed task speech not triggered"
    # Check that the missed one-time task was removed from the store
    assert all(t.label != "GracefulMiss" for t in store.tasks), "Missed one-time task not removed"
