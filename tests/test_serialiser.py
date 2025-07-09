"""
Unit tests for serialiser.py in PlanFlow add-on.
"""
from datetime import datetime, timedelta
from addon.globalPlugins.planflow.task.serialiser import parse_interval, to_dict, from_dict
from addon.globalPlugins.planflow.task.model import ScheduledTask


def test_parse_interval_seconds() -> None:
    """
    Test that parse_interval correctly parses seconds intervals.
    """
    assert parse_interval("10s") == timedelta(seconds=10)


def test_parse_interval_minutes() -> None:
    """
    Test that parse_interval correctly parses minutes intervals.
    """
    assert parse_interval("2m") == timedelta(minutes=2)


def test_parse_interval_hours() -> None:
    """
    Test that parse_interval correctly parses hours intervals.
    """
    assert parse_interval("1h") == timedelta(hours=1)


def test_to_dict_and_from_dict() -> None:
    """
    Test that to_dict and from_dict correctly serialize and deserialize ScheduledTask.
    """
    dt = datetime(2025, 7, 9, 12, 0, 0)
    task = ScheduledTask(
        id="abc123",
        label="Test Task",
        time=dt,
        description="desc",
        link="http://example.com",
        recurrence=timedelta(days=1),
        callback=None,
    )
    data = to_dict(task)
    restored = from_dict(data)
    # Check that all fields are preserved after round-trip serialization
    assert restored.id == task.id
    assert restored.label == task.label
    assert restored.time == task.time
    assert restored.description == task.description
    assert restored.link == task.link
    assert restored.recurrence == task.recurrence
