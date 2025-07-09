"""
Tests for thread management in Scheduler:
- No duplicate threads on repeated .start()
- Scheduler thread stops cleanly
"""


from datetime import datetime, timedelta
from pathlib import Path
import pytest
from addon.globalPlugins.planflow.task.schedule import Scheduler
from addon.globalPlugins.planflow.task.model import ScheduledTask
from addon.globalPlugins.planflow.task.store import TaskStore
from collections.abc import Callable
from tests.utils.dummies import DummySpeech


@pytest.fixture
def speech() -> DummySpeech:
    """Fixture that provides a DummySpeech instance for capturing speech output in tests."""
    return DummySpeech()
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



def test_scheduler_starts_and_stops_cleanly(speech: DummySpeech, store: TaskStore) -> None:
    """
    Ensure APScheduler starts and stops without errors and no duplicate threads.
    """
    task = make_task("CleanStartStop", datetime.now() + timedelta(seconds=1))
    store.add(task)
    sched = Scheduler(store=store, speech_callback=speech)
    assert not sched.is_running, "Scheduler should not be running initially"
    sched.schedule_all()
    sched.start()
    assert sched.is_running, "Scheduler did not start properly"
    # Repeated start should not cause error or duplication
    sched.start()
    assert sched.is_running, "Scheduler became inactive after second start"
    sched.stop()
    assert not sched.is_running, "Scheduler did not stop properly"


def test_scheduler_start_twice_no_error(speech: DummySpeech, store: TaskStore) -> None:
    """
    Ensure calling start() multiple times doesn't raise or duplicate scheduler.
    """
    sched = Scheduler(store=store, speech_callback=speech)
    sched.start()
    sched.start()  # Should be idempotent
    assert sched.is_running, "Scheduler is not running after repeated starts"
    sched.stop()
