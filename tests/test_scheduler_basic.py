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



@pytest.fixture
def speech() -> DummySpeech:
    """Fixture providing a dummy speech callback."""
    return DummySpeech()





def test_callback_and_speech_called(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Test that both callback and speech are triggered for a scheduled task.
    """
    due = datetime.now() + timedelta(seconds=1)
    task = make_task("Speech+Callback", due, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(2)
    sched.stop()
    # Check that the callback was called
    assert callback.called, "Callback was not called"
    # Check that the speech callback was called with the correct message
    assert any("Speech+Callback" in m for m in speech.messages), "Speech not called"



def test_task_runs_after_minimal_delay(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Test that a task scheduled with minimal delay runs and triggers callbacks.
    """
    due = datetime.now() + timedelta(milliseconds=500)
    task = make_task("Quick Task", due, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(1)
    sched.stop()
    # Check that the callback was called for the quick task
    assert callback.called, "Callback was not called for quick task"
    # Check that the speech callback was called for the quick task
    assert any("Quick Task" in m for m in speech.messages), "Speech not called for quick task"
