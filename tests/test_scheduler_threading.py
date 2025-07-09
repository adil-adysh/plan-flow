"""
Tests for thread management in Scheduler:
- No duplicate threads on repeated .start()
- Scheduler thread stops cleanly
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
def db_path(tmp_path):
    return tmp_path / "db.json"


@pytest.fixture
def store(db_path):
    return TaskStore(file_path=str(db_path))


def test_stop_scheduler_stops_thread(speech, store):
    due = datetime.now() + timedelta(seconds=2)
    task = make_task("StopTest", due)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    sched.stop()
    thread = sched._thread
    assert thread is None or not thread.is_alive(), "Scheduler thread did not stop properly"


def test_scheduler_does_not_duplicate_running_thread(speech, store):
    due = datetime.now() + timedelta(seconds=1)
    task = make_task("ThreadSafe", due)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    thread1 = sched._thread
    sched.start()  # Should be ignored
    thread2 = sched._thread
    time.sleep(2)
    sched.stop()
    assert thread1 is thread2, "Scheduler started a second thread unnecessarily"
    assert not thread1.is_alive(), "Scheduler thread did not stop after .stop()"
