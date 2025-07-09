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


def test_missed_task(speech, store):
    due = datetime.now() - timedelta(seconds=5)
    task = make_task("Missed Task", due)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    assert any("missed a task" in m for m in speech.messages), "Missed task not reported"
    assert any("will not recur" in m for m in speech.messages), "Non-recurring task removal not reported"
    assert not any(t.label == "Missed Task" for t in store.tasks), "Missed one-time task not removed"


def test_missed_recurring_task_reschedules_correctly(speech, callback, store):
    due = datetime.now() - timedelta(seconds=3)
    task = make_task("MissedRecurring", due, recurrence=timedelta(seconds=2), callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(3)
    sched.stop()
    assert callback.called, "Missed recurring task callback not called"
    assert any("Reminder: MissedRecurring" in m for m in speech.messages), "Reminder message missing for missed recurring task"


def test_scheduler_gracefully_handles_past_task_without_callback(speech, store):
    due = datetime.now() - timedelta(minutes=1)
    task = make_task("GracefulMiss", due)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    assert any("GracefulMiss" in m for m in speech.messages), "Missed task speech not triggered"
    assert all(t.label != "GracefulMiss" for t in store.tasks), "Missed one-time task not removed"
