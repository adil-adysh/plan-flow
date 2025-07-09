import pytest
from datetime import datetime, timedelta
from addon.globalPlugins.planflow.task.model import ScheduledTask

def test_task_has_unique_id():
    task1 = ScheduledTask()
    task2 = ScheduledTask()
    assert task1.id != task2.id

def test_default_label_is_empty():
    task = ScheduledTask()
    assert task.label == ""

def test_is_due_true_now():
    now = datetime.now()
    task = ScheduledTask(time=now - timedelta(seconds=1))
    assert task.is_due()

def test_is_due_false_future():
    now = datetime.now()
    task = ScheduledTask(time=now + timedelta(minutes=5))
    assert not task.is_due(ref=now)

def test_recurrence_can_be_set():
    recurrence = timedelta(days=1)
    task = ScheduledTask(recurrence=recurrence)
    assert task.recurrence == recurrence

def test_callback_can_be_set_and_invoked():
    called = []

    def cb():
        called.append(True)

    task = ScheduledTask(callback=cb)
    assert task.callback is cb
    task.callback()
    assert called == [True]
