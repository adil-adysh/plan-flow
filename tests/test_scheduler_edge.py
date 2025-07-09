"""
Edge case tests for Scheduler:
- Task scheduled exactly at now
- Task callback raising exception
- Multiple tasks executing in one run
"""

import time
import threading
import logging
import pytest
from unittest import mock
from datetime import datetime, timedelta
from collections.abc import Callable

from addon.globalPlugins.planflow.task.schedule import Scheduler
from addon.globalPlugins.planflow.task.model import ScheduledTask
from addon.globalPlugins.planflow.task.store import TaskStore

from tests.utils.dummies import DummySpeech, DummyCallback

logger = logging.getLogger(__name__)


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


@pytest.mark.edge
def test_task_with_exact_now_execution(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    A task scheduled for "now" should be executed shortly after scheduling.
    """
    triggered = threading.Event()

    def wrapped_callback() -> None:
        logger.info("NowTask callback triggered.")
        callback()
        triggered.set()

    task_time = datetime.now() + timedelta(milliseconds=200)
    task = make_task("NowTask", task_time, callback=wrapped_callback)
    store.add(task)

    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()

    triggered.wait(timeout=5)
    sched.stop()

    assert callback.called, "Callback for now-execution task not triggered"
    assert any("Reminder: NowTask" in m for m in speech.messages), "Speech not triggered for now-scheduled task"


@pytest.mark.edge
def test_non_positive_delay_task_executes_with_minimum_delay(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    A task scheduled just in the past should still run quickly.
    """
    triggered = threading.Event()

    def wrapped_callback() -> None:
        callback()
        triggered.set()

    past_time = datetime.now() + timedelta(milliseconds=100)
    task = make_task("EdgeNow", past_time, callback=wrapped_callback)
    store.add(task)

    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()

    triggered.wait(timeout=5)
    sched.stop()

    assert callback.called, "Past-due task did not execute"
    assert any("Reminder: EdgeNow" in m for m in speech.messages), "Speech not triggered for past-due task"


@pytest.mark.edge
def test_task_callback_exception_does_not_crash_scheduler(
    speech: DummySpeech, store: TaskStore
) -> None:
    """
    A task callback that raises an exception should not crash the scheduler.
    Speech reminder must still be triggered.
    """
    triggered = threading.Event()

    class ExplodingCallback:
        def __init__(self) -> None:
            self.called = False

        def __call__(self) -> None:
            self.called = True
            triggered.set()
            raise RuntimeError("Simulated failure")

    cb = ExplodingCallback()
    task_time = datetime.now() + timedelta(milliseconds=200)
    task = make_task("Exploding", task_time, callback=cb)
    store.add(task)

    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()

    triggered.wait(timeout=5)
    sched.stop()

    assert cb.called, "Exploding callback was never called"
    assert any("Reminder: Exploding" in m for m in speech.messages), "Reminder for exploding callback not spoken"


@pytest.mark.edge
def test_scheduling_multiple_tasks_executes_all(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Multiple scheduled tasks should each trigger their callbacks and reminders.
    """
    event1 = threading.Event()

    def wrapped_callback() -> None:
        callback()
        event1.set()

    due1 = datetime.now() + timedelta(milliseconds=300)
    due2 = datetime.now() + timedelta(milliseconds=600)

    task1 = make_task("Multi1", due1, callback=wrapped_callback)
    task2 = make_task("Multi2", due2)

    store.add(task1)
    store.add(task2)

    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()

    event1.wait(timeout=5)
    time.sleep(1)
    sched.stop()

    assert callback.called, "Callback for Multi1 not triggered"
    assert any("Reminder: Multi1" in m for m in speech.messages), "Reminder for Multi1 missing"
    assert any("Reminder: Multi2" in m for m in speech.messages), "Reminder for Multi2 missing"
