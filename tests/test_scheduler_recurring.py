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


class DummySpeech:
    def __init__(self):
        self.messages: list[str] = []

    def __call__(self, msg: str) -> None:
        self.messages.append(msg)


class DummyCallback:
    def __init__(self):
        self.called = False

    def __call__(self):
        self.called = True


def make_task(
    label: str,
    due: datetime,
    recurrence: timedelta | None = None,
    callback: Callable[[], None] | None = None
) -> ScheduledTask:
    task = ScheduledTask(label=label, time=due, recurrence=recurrence)
    if callback:
        task.callback = callback
    return task


@pytest.fixture
def speech():
    return DummySpeech()


@pytest.fixture
def callback():
    return DummyCallback()


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "db.json"


@pytest.fixture
def store(db_path):
    return TaskStore(file_path=str(db_path))


def test_recurring_task_runs_multiple_times(speech, callback, store):
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


def test_task_reschedule_after_recurrence_persists_in_store(speech, callback, store):
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
