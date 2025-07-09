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



def test_task_with_exact_now_execution(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Test that a task scheduled exactly at the current time executes immediately.
    """
    task = make_task("NowTask", datetime.now(), callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(2)
    sched.stop()
    # Check that the callback was called for the now-execution task
    assert callback.called, "Callback for now-execution task not triggered"
    # Check that the speech callback was called for the now-scheduled task
    assert any("Reminder: NowTask" in m for m in speech.messages), "Speech not triggered for now-scheduled task"



def test_non_positive_delay_task_executes_with_minimum_delay(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Test that a task scheduled in the past executes with a minimum fallback delay.
    """
    due = datetime.now() - timedelta(milliseconds=100)
    task = make_task("EdgeNow", due, callback=callback)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    time.sleep(2)
    sched.stop()
    # Check that the callback was called for the edge case task
    assert callback.called, "Task with past time did not execute using fallback delay"
    # Check that the speech callback was called for the edge case task
    assert any("Reminder: EdgeNow" in m for m in speech.messages), "Speech not triggered for edge case task"



def test_task_callback_exception_does_not_crash_scheduler(
    speech: DummySpeech, store: TaskStore
) -> None:
    """
    Test that an exception in a task callback does not crash the scheduler and the reminder is still spoken.
    """
    class ExplodingCallback:
        def __init__(self) -> None:
            super().__init__()  # For linter/type checker compliance
            self.called: bool = False

        def __call__(self) -> None:
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
    # Check that the callback was called even though it raised
    assert cb.called, "Exploding callback was never called"
    # Check that the reminder was still spoken
    assert any("Reminder: Exploding" in m for m in speech.messages), "Reminder for exploding callback not spoken"



def test_scheduling_multiple_tasks_executes_all(
    speech: DummySpeech, callback: DummyCallback, store: TaskStore
) -> None:
    """
    Test that scheduling multiple tasks results in all tasks being executed and callbacks/speech triggered.
    """
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
    # Check that both reminders were spoken
    assert any("Reminder: Multi1" in m for m in speech.messages), "Task 1 reminder missing"
    assert any("Reminder: Multi2" in m for m in speech.messages), "Task 2 reminder missing"
    # Check that the callback for the first task was called
    assert callback.called, "Task 1 callback not triggered"
