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
    """Dummy speech callback for capturing speech messages in tests."""
    def __init__(self) -> None:
        super().__init__()  # For linter/type checker compliance
        self.messages: list[str] = []

    def __call__(self, msg: str) -> None:
        """Capture a speech message."""
        self.messages.append(msg)



class DummyCallback:
    """Dummy callback for tracking invocation in tests."""
    def __init__(self) -> None:
        super().__init__()  # For linter/type checker compliance
        self.called: bool = False

    def __call__(self) -> None:
        """Mark the callback as called."""
        self.called = True



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



def test_schedule_and_run_single_task(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Test that a single scheduled task runs when due, triggers speech and callback.
    """
    due = datetime.now() + timedelta(seconds=2)
    task = make_task("Test Task", due, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(3)
    sched.stop()
    # Check that the reminder message was spoken
    assert any("Reminder: Test Task" in m for m in speech.messages), "Reminder message not found"
    # Check that the callback was called
    assert callback.called, "Callback was not called"



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
