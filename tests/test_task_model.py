"""
Unit tests for the Task Model data classes in PlanFlow.

Covers: TaskDefinition, RetryPolicy, TaskOccurrence, TaskExecution, TaskEvent, TimeSlot, WorkingHours.
"""

import pytest
from datetime import datetime, timedelta, time
from addon.globalPlugins.planflow.task.task_model import (
    TaskDefinition,
    RetryPolicy,
    TaskOccurrence,
    TaskExecution,
    TaskEvent,
    TimeSlot,
    WorkingHours,
)
from dataclasses import asdict

@pytest.fixture
def sample_retry_policy() -> RetryPolicy:
    return RetryPolicy(max_retries=3)

@pytest.fixture
def sample_task_def(sample_retry_policy: RetryPolicy) -> TaskDefinition:
    return TaskDefinition(
        id="task-1",
        title="Test Task",
        description="A test task.",
        link="http://example.com",
        created_at=datetime(2025, 7, 10, 12, 0, 0),
        recurrence=timedelta(days=1),
        priority="high",
        preferred_slots=["morning", "afternoon"],
        retry_policy=sample_retry_policy,
    )

@pytest.fixture
def sample_occurrence() -> TaskOccurrence:
    return TaskOccurrence(
        id="occ-1",
        task_id="task-1",
        scheduled_for=datetime(2025, 7, 11, 9, 0, 0),
        slot_name="morning",
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
    assert sample_task_def.priority == "high"
    assert sample_task_def.preferred_slots == ["morning", "afternoon"]
    assert isinstance(sample_task_def.retry_policy, RetryPolicy)

def test_retry_policy_fields(sample_retry_policy: RetryPolicy):
    assert sample_retry_policy.max_retries == 3

def test_task_occurrence_fields(sample_occurrence: TaskOccurrence):
    assert sample_occurrence.id == "occ-1"
    assert sample_occurrence.task_id == "task-1"
    assert sample_occurrence.scheduled_for == datetime(2025, 7, 11, 9, 0, 0)
    assert sample_occurrence.slot_name == "morning"

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
    assert isinstance(sample_execution.is_reschedulable, bool)
    assert sample_execution.is_reschedulable is True
    assert isinstance(sample_execution.retry_count, int)
    assert sample_execution.last_event_time == sample_execution.history[-1].timestamp

def test_task_execution_reschedulable_logic():
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
    exec_no_retries = TaskExecution(
        occurrence_id="occ-4",
        state="pending",
        retries_remaining=0,
        history=[],
    )
    assert exec_no_retries.is_reschedulable is False

def test_time_slot_fields():
    slot = TimeSlot(name="morning", start=time(8, 0), end=time(12, 0))
    assert slot.name == "morning"
    assert slot.start == time(8, 0)
    assert slot.end == time(12, 0)

def test_working_hours_fields():
    wh = WorkingHours(
        day="monday",
        start=time(8, 0),
        end=time(17, 0),
        allowed_slots=["morning", "afternoon"]
    )
    assert wh.day == "monday"
    assert wh.start == time(8, 0)
    assert wh.end == time(17, 0)
    assert wh.allowed_slots == ["morning", "afternoon"]

def test_serialization_roundtrip(sample_task_def: TaskDefinition, sample_occurrence: TaskOccurrence, sample_event: TaskEvent, sample_execution: TaskExecution):
    for obj in [sample_task_def, sample_occurrence, sample_event, sample_execution]:
        d = asdict(obj)
        assert isinstance(d, dict)
        for v in d.values():
            assert not callable(v)

def test_task_event_enum():
    allowed = ("triggered", "missed", "rescheduled", "completed")
    for val in allowed:
        ev = TaskEvent(event=val, timestamp=datetime.now())
        assert ev.event in allowed
