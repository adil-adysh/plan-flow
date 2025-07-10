"""Tests for RecoveryService: missed task rescheduling, retry exhaustion, recurrence behavior, and pinned occurrence exclusion."""

import pytest
from datetime import datetime, timedelta, time
from addon.globalPlugins.planflow.task.recovery_service import RecoveryService
from addon.globalPlugins.planflow.task.task_model import (
    TaskDefinition, TaskOccurrence, TaskExecution, RetryPolicy, WorkingHours, TimeSlot, TaskEvent
)
from addon.globalPlugins.planflow.task.calendar_planner import CalendarPlanner

@pytest.fixture
def sample_working_hours() -> list[WorkingHours]:
    return [
        WorkingHours(day="monday", start=time(9, 0), end=time(17, 0), allowed_slots=["morning", "afternoon"]),
        WorkingHours(day="tuesday", start=time(9, 0), end=time(17, 0), allowed_slots=["morning", "afternoon"]),
    ]

@pytest.fixture
def sample_slot_pool() -> list[TimeSlot]:
    return [
        TimeSlot(name="morning", start=time(9, 0), end=time(12, 0)),
        TimeSlot(name="afternoon", start=time(13, 0), end=time(17, 0)),
    ]

@pytest.fixture
def calendar() -> CalendarPlanner:
    return CalendarPlanner()

@pytest.fixture
def now() -> datetime:
    return datetime(2025, 7, 7, 10, 0, 0)  # Monday

@pytest.fixture
def base_task(now) -> TaskDefinition:
    return TaskDefinition(
        id="task1",
        title="Test Task",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=2),
    )

@pytest.fixture
def scheduled_occurrences(now, base_task) -> list[TaskOccurrence]:
    return [
        TaskOccurrence(
            id="occ1",
            task_id=base_task.id,
            scheduled_for=now.replace(hour=9, minute=0),
            slot_name="morning",
            pinned_time=None,
        )
    ]

@pytest.fixture
def base_occurrence(now, base_task) -> TaskOccurrence:
    return TaskOccurrence(
        id="occ1",
        task_id=base_task.id,
        scheduled_for=now - timedelta(hours=2),
        slot_name="morning",
        pinned_time=None,
    )

@pytest.fixture
def base_execution(base_occurrence) -> TaskExecution:
    return TaskExecution(
        occurrence_id=base_occurrence.id,
        state="missed",
        retries_remaining=1,
        history=[TaskEvent(event="missed", timestamp=base_occurrence.scheduled_for)],
    )

def test_retry_scheduled(calendar, now, base_task, base_occurrence, base_execution, sample_working_hours, sample_slot_pool, scheduled_occurrences):
    service = RecoveryService()
    executions = [base_execution]
    occurrences = {base_occurrence.id: base_occurrence}
    tasks = {base_task.id: base_task}
    result = service.recover_missed_occurrences(
        executions,
        occurrences,
        tasks,
        now,
        calendar,
        scheduled_occurrences,
        sample_working_hours,
        sample_slot_pool,
        max_per_day=3
    )
    assert len(result) == 1
    assert result[0].task_id == base_task.id
    assert result[0].scheduled_for > now

def test_retry_fails_due_to_no_slots(calendar, now, base_task, base_occurrence, base_execution, sample_working_hours, scheduled_occurrences):
    service = RecoveryService()
    executions = [base_execution]
    occurrences = {base_occurrence.id: base_occurrence}
    tasks = {base_task.id: base_task}
    # Provide empty slot pool
    result = service.recover_missed_occurrences(
        executions,
        occurrences,
        tasks,
        now,
        calendar,
        scheduled_occurrences,
        sample_working_hours,
        [],
        max_per_day=3
    )
    assert result == []

def test_recurrence_scheduled(calendar, now, base_task, base_occurrence, sample_working_hours, sample_slot_pool, scheduled_occurrences):
    service = RecoveryService()
    executions = [
        TaskExecution(
            occurrence_id=base_occurrence.id,
            state="missed",
            retries_remaining=0,
            history=[TaskEvent(event="missed", timestamp=base_occurrence.scheduled_for)],
        )
    ]
    occurrences = {base_occurrence.id: base_occurrence}
    tasks = {base_task.id: base_task}
    result = service.recover_missed_occurrences(
        executions,
        occurrences,
        tasks,
        now,
        calendar,
        scheduled_occurrences,
        sample_working_hours,
        sample_slot_pool,
        max_per_day=3
    )
    assert len(result) == 1
    assert result[0].task_id == base_task.id
    assert result[0].scheduled_for > now

def test_retry_limit_exceeded(calendar, now, base_task, base_occurrence, sample_working_hours, sample_slot_pool, scheduled_occurrences):
    service = RecoveryService()
    executions = [
        TaskExecution(
            occurrence_id=base_occurrence.id,
            state="missed",
            retries_remaining=0,
            history=[TaskEvent(event="missed", timestamp=base_occurrence.scheduled_for)],
        )
    ]
    occurrences = {base_occurrence.id: base_occurrence}
    tasks = {base_task.id: base_task}
    result = service.recover_missed_occurrences(
        executions,
        occurrences,
        tasks,
        now,
        calendar,
        scheduled_occurrences,
        sample_working_hours,
        sample_slot_pool,
        max_per_day=3
    )
    assert result  # Recurrence should be scheduled, not retry
    assert all(occ.scheduled_for > now for occ in result)

def test_pinned_occurrence_ignored(calendar, now, base_task, sample_working_hours, sample_slot_pool, scheduled_occurrences):
    service = RecoveryService()
    pinned_occ = TaskOccurrence(
        id="occ2",
        task_id=base_task.id,
        scheduled_for=now - timedelta(hours=2),
        slot_name="morning",
        pinned_time=now - timedelta(hours=2),
    )
    executions = [
        TaskExecution(
            occurrence_id=pinned_occ.id,
            state="missed",
            retries_remaining=1,
            history=[TaskEvent(event="missed", timestamp=pinned_occ.scheduled_for)],
        )
    ]
    occurrences = {pinned_occ.id: pinned_occ}
    tasks = {base_task.id: base_task}
    result = service.recover_missed_occurrences(
        executions,
        occurrences,
        tasks,
        now,
        calendar,
        scheduled_occurrences,
        sample_working_hours,
        sample_slot_pool,
        max_per_day=3
    )
    assert result == []

def test_working_hour_limit_prevents_scheduling(calendar, now, base_task, base_occurrence, base_execution, scheduled_occurrences):
    service = RecoveryService()
    executions = [base_execution]
    occurrences = {base_occurrence.id: base_occurrence}
    tasks = {base_task.id: base_task}
    # Provide working hours that do not include now or next recurrence
    working_hours = [WorkingHours(day="wednesday", start=time(9, 0), end=time(17, 0), allowed_slots=["morning"])]
    slot_pool = [TimeSlot(name="morning", start=time(9, 0), end=time(12, 0))]
    result = service.recover_missed_occurrences(
        executions,
        occurrences,
        tasks,
        now,
        calendar,
        scheduled_occurrences,
        working_hours,
        slot_pool,
        max_per_day=3
    )
    assert result == []
