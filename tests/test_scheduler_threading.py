"""
Tests for thread management in Scheduler:
- No duplicate threads on repeated .start()
- Scheduler thread stops cleanly
"""


import time
from datetime import datetime, timedelta
from pathlib import Path
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


# Included for completeness and consistency with other test files
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
    task = ScheduledTask(label=label, time=due, recurrence=recurrence)
    if callback:
        task.callback = callback
    return task


@pytest.fixture
def speech() -> DummySpeech:
    """
    Fixture that provides a DummySpeech instance for capturing speech output in tests.
    """
    return DummySpeech()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """
    Fixture that provides a temporary file path for the TaskStore database.
    """
    return str(tmp_path / "db.json")


@pytest.fixture
def store(db_path: str) -> TaskStore:
    """
    Fixture that provides a TaskStore instance using a temporary database file.
    """
    return TaskStore(file_path=db_path)


def test_stop_scheduler_stops_thread(speech: DummySpeech, store: TaskStore) -> None:
    """
    Test that the scheduler thread stops cleanly after calling stop().
    Ensures no thread is left running after stop is called.
    """
    # Schedule a task and start the scheduler, then stop it and check the thread is stopped.
    due = datetime.now() + timedelta(seconds=2)
    task = make_task("StopTest", due)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    sched.stop()
    # Accessing protected member for test purposes; Scheduler does not expose thread status publicly.
    thread = sched._thread  # type: ignore[attr-defined]
    assert thread is None or not thread.is_alive(), "Scheduler thread did not stop properly"


def test_scheduler_does_not_duplicate_running_thread(speech: DummySpeech, store: TaskStore) -> None:
    """
    Test that calling start() multiple times does not create duplicate threads.
    Ensures only one scheduler thread runs at a time.
    """
    # Start the scheduler twice and ensure only one thread is created and stopped.
    due = datetime.now() + timedelta(seconds=1)
    task = make_task("ThreadSafe", due)
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    sched.schedule_all()
    sched.start()
    # Accessing protected member for test purposes; Scheduler does not expose thread status publicly.
    thread1 = sched._thread  # type: ignore[attr-defined]
    sched.start()  # Should be ignored
    thread2 = sched._thread  # type: ignore[attr-defined]
    time.sleep(2)
    sched.stop()
    assert thread1 is thread2, "Scheduler started a second thread unnecessarily"
    assert thread1 is not None and not thread1.is_alive(), "Scheduler thread did not stop after .stop()"
