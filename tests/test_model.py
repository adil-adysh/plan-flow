"""
Unit tests for ScheduledTask in model.py.
Ensures correct default values, unique IDs, due logic, recurrence, and callback behavior.
"""

import pytest
from datetime import datetime, timedelta
from addon.globalPlugins.planflow.task.model import ScheduledTask

def test_task_has_unique_id() -> None:
    """Each ScheduledTask should have a unique id."""
    task1 = ScheduledTask()
    task2 = ScheduledTask()
    assert task1.id != task2.id

def test_default_label_is_empty() -> None:
    """Default label should be an empty string."""
    task = ScheduledTask()
    assert task.label == ""

def test_is_due_true_now() -> None:
    """Task is due if time is in the past."""
    now = datetime.now()
    task = ScheduledTask(time=now - timedelta(seconds=1))
    assert task.is_due(ref=now)

def test_is_due_false_future() -> None:
    """Task is not due if time is in the future."""
    now = datetime.now()
    task = ScheduledTask(time=now + timedelta(minutes=5))
    assert not task.is_due(ref=now)

def test_recurrence_can_be_set() -> None:
    """Recurrence can be set and retrieved."""
    recurrence = timedelta(days=1)
    task = ScheduledTask(recurrence=recurrence)
    assert task.recurrence == recurrence

def test_callback_can_be_set_and_invoked() -> None:
    """Callback can be set and invoked."""
    called: list[bool] = []
    def cb() -> None:
        called.append(True)
    task = ScheduledTask(callback=cb)
    assert task.callback is cb
    if task.callback is not None:
        task.callback()
    assert called == [True]

def test_callback_is_none_by_default() -> None:
    """Callback should be None by default."""
    task = ScheduledTask()
    assert task.callback is None
