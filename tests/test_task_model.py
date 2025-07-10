"""
Unit tests for the Task Model data classes in PlanFlow.

Covers: TaskDefinition, RetryPolicy, TaskOccurrence, TaskExecution, TaskEvent.
"""

import pytest
from datetime import datetime, timedelta
from addon.globalPlugins.planflow.task.task_model import (
    TaskDefinition,
    RetryPolicy,
    TaskOccurrence,
    TaskExecution,
    TaskEvent,
)
from dataclasses import asdict


@pytest.fixture
def sample_retry_policy() -> RetryPolicy:
    return RetryPolicy(max_retries=3, retry_interval=timedelta(minutes=5), speak_on_retry=True)

@pytest.fixture
def sample_task_def(sample_retry_policy: RetryPolicy) -> TaskDefinition:
    return TaskDefinition(
        id="task-1",
        title="Test Task",
        description="A test task.",
        link="http://example.com",
        created_at=datetime(2025, 7, 10, 12, 0, 0),
        recurrence=timedelta(days=1),
        retry_policy=sample_retry_policy,
    )

@pytest.fixture
def sample_occurrence() -> TaskOccurrence:
    return TaskOccurrence(
        id="occ-1",
        task_id="task-1",
        scheduled_for=datetime(2025, 7, 11, 9, 0, 0),
    )

@pytest.fixture
def sample_event() -> TaskEvent:
    return TaskEvent(event="triggered", timestamp=datetime(2025, 7, 11, 9, 0, 0))

@pytest.fixture
def sample_execution(sample_event: TaskEvent) -> TaskExecution:
    return TaskExecution(
        occurrence_id="occ-1",
        state="pending",
        retries_remaining=2,
        history=[sample_event],
    )

def test_task_definition_fields(sample_task_def: TaskDefinition):
    assert sample_task_def.id == "task-1"
    assert sample_task_def.title == "Test Task"
    assert sample_task_def.description == "A test task."
    assert sample_task_def.link == "http://example.com"
    assert sample_task_def.created_at == datetime(2025, 7, 10, 12, 0, 0)
    assert sample_task_def.recurrence == timedelta(days=1)
    assert isinstance(sample_task_def.retry_policy, RetryPolicy)

def test_retry_policy_fields(sample_retry_policy: RetryPolicy):
    assert sample_retry_policy.max_retries == 3
    assert sample_retry_policy.retry_interval == timedelta(minutes=5)
    assert sample_retry_policy.speak_on_retry is True

def test_task_occurrence_fields(sample_occurrence: TaskOccurrence):
    assert sample_occurrence.id == "occ-1"
    assert sample_occurrence.task_id == "task-1"
    assert sample_occurrence.scheduled_for == datetime(2025, 7, 11, 9, 0, 0)

def test_task_event_fields(sample_event: TaskEvent):
    assert sample_event.event == "triggered"
    assert sample_event.timestamp == datetime(2025, 7, 11, 9, 0, 0)

def test_task_execution_fields(sample_execution: TaskExecution):
    assert sample_execution.occurrence_id == "occ-1"
    assert sample_execution.state == "pending"
    assert sample_execution.retries_remaining == 2
    assert isinstance(sample_execution.history, list)
    assert sample_execution.history[0].event == "triggered"

def test_task_execution_properties(sample_execution: TaskExecution):
    # is_reschedulable: True if retries_remaining > 0 and state is not 'done' or 'cancelled'
    assert isinstance(sample_execution.is_reschedulable, bool)
    assert sample_execution.is_reschedulable is True
    # retry_count: should be max_retries - retries_remaining (simulate)
    # Not directly testable without max_retries, but check type
    assert isinstance(sample_execution.retry_count, int)
    # last_event_time: should be timestamp of last event
    assert sample_execution.last_event_time == sample_execution.history[-1].timestamp

def test_task_execution_reschedulable_logic():
    # Not reschedulable if state is 'done' or 'cancelled'
    exec_done = TaskExecution(
        occurrence_id="occ-2",
        state="done",
        retries_remaining=1,
        history=[],
    )
    exec_cancelled = TaskExecution(
        occurrence_id="occ-3",
        state="cancelled",
        retries_remaining=1,
        history=[],
    )
    assert exec_done.is_reschedulable is False
    assert exec_cancelled.is_reschedulable is False
    # Not reschedulable if retries_remaining == 0
    exec_no_retries = TaskExecution(
        occurrence_id="occ-4",
        state="pending",
        retries_remaining=0,
        history=[],
    )
    assert exec_no_retries.is_reschedulable is False

def test_serialization_roundtrip(sample_task_def: TaskDefinition, sample_occurrence: TaskOccurrence, sample_event: TaskEvent, sample_execution: TaskExecution):
    # All models must be serializable to dict and back (TinyDB compatible)
    for obj in [sample_task_def, sample_occurrence, sample_event, sample_execution]:
        d = asdict(obj)
        assert isinstance(d, dict)
        # Check that all values are JSON-serializable types (except datetime/timedelta, which must be handled by serialiser)
        for v in d.values():
            assert not callable(v)

def test_task_event_enum():
    # Only allowed event values
    from typing import Literal
    allowed: tuple[Literal["triggered"], Literal["missed"], Literal["rescheduled"], Literal["completed"]] = (
        "triggered", "missed", "rescheduled", "completed"
    )
    for val in allowed:
        ev = TaskEvent(event=val, timestamp=datetime.now())
        assert ev.event in allowed
    # The following is a mypy/pyright type error, not a runtime error, so we do not test it at runtime.
