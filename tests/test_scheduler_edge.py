"""
Edge case tests for Scheduler:
- Task scheduled exactly at now
- Task callback raising exception
- Multiple tasks executing in one run
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


def test_task_with_exact_now_execution(speech, callback, store):
    task = make_task("NowTask", datetime.now(), callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(2)
    sched.stop()
    assert callback.called, "Callback for now-execution task not triggered"
    assert any("Reminder: NowTask" in m for m in speech.messages), "Speech not triggered for now-scheduled task"


def test_non_positive_delay_task_executes_with_minimum_delay(speech, callback, store):
    due = datetime.now() - timedelta(milliseconds=100)
    task = make_task("EdgeNow", due, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(2)
    sched.stop()
    assert callback.called, "Task with past time did not execute using fallback delay"
    assert any("Reminder: EdgeNow" in m for m in speech.messages), "Speech not triggered for edge case task"


def test_task_callback_exception_does_not_crash_scheduler(speech, store):
    class ExplodingCallback:
        def __init__(self):
            self.called = False

        def __call__(self):
            self.called = True
            raise RuntimeError("Simulated failure")

    cb = ExplodingCallback()
    task = make_task("Exploding", datetime.now() + timedelta(seconds=1), callback=cb)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(2)
    sched.stop()
    assert cb.called, "Exploding callback was never called"
    assert any("Reminder: Exploding" in m for m in speech.messages), "Reminder for exploding callback not spoken"


def test_scheduling_multiple_tasks_executes_all(speech, callback, store):
    due1 = datetime.now() + timedelta(seconds=1)
    due2 = datetime.now() + timedelta(seconds=2)
    task1 = make_task("Multi1", due1, callback=callback)
    task2 = make_task("Multi2", due2)
    store.add(task1)
    store.add(task2)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(3)
    sched.stop()
    assert any("Reminder: Multi1" in m for m in speech.messages), "Task 1 reminder missing"
    assert any("Reminder: Multi2" in m for m in speech.messages), "Task 2 reminder missing"
    assert callback.called, "Task 1 callback not triggered"
