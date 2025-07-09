"""
Basic Scheduler tests:
- Task runs when due
- Speech and callback are triggered
- Tasks execute after minimal delay
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


def test_schedule_and_run_single_task(speech, callback, store):
    due = datetime.now() + timedelta(seconds=2)
    task = make_task("Test Task", due, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(3)
    sched.stop()
    assert any("Reminder: Test Task" in m for m in speech.messages), "Reminder message not found"
    assert callback.called, "Callback was not called"


def test_callback_and_speech_called(speech, callback, store):
    due = datetime.now() + timedelta(seconds=1)
    task = make_task("Speech+Callback", due, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(2)
    sched.stop()
    assert callback.called, "Callback was not called"
    assert any("Speech+Callback" in m for m in speech.messages), "Speech not called"


def test_task_runs_after_minimal_delay(speech, callback, store):
    due = datetime.now() + timedelta(milliseconds=500)
    task = make_task("Quick Task", due, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(1)
    sched.stop()
    assert callback.called, "Callback was not called for quick task"
    assert any("Quick Task" in m for m in speech.messages), "Speech not called for quick task"
