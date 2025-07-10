"""Unit tests for TaskScheduler in PlanFlow NVDA add-on.

Covers due/missed detection, recurrence, retry logic, and rescheduling.
"""

import pytest
from datetime import datetime, timedelta
from addon.globalPlugins.planflow.task.scheduler_service import TaskScheduler
from addon.globalPlugins.planflow.task.task_model import TaskDefinition, TaskOccurrence, RetryPolicy

@pytest.fixture
def sample_task_def() -> TaskDefinition:
    return TaskDefinition(
        id="task1",
        title="Test Task",
        description=None,
        link=None,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        recurrence=timedelta(days=1),
        retry_policy=RetryPolicy(max_retries=2, retry_interval=timedelta(hours=1), speak_on_retry=True),
    )

@pytest.fixture
def sample_occurrence() -> TaskOccurrence:
    return TaskOccurrence(
        id="task1:123456",
        task_id="task1",
        scheduled_for=datetime(2024, 1, 2, 9, 0, 0),
    )

@pytest.fixture
def sample_retry_policy() -> RetryPolicy:
    return RetryPolicy(max_retries=3, retry_interval=timedelta(minutes=30), speak_on_retry=False)

@pytest.mark.parametrize("now,expected", [
    (datetime(2024, 1, 2, 9, 0, 0), True),
    (datetime(2024, 1, 2, 8, 59, 59), False),
])
def test_is_due_edge_cases(sample_occurrence: TaskOccurrence, now: datetime, expected: bool) -> None:
    scheduler = TaskScheduler()
    assert scheduler.is_due(sample_occurrence, now) is expected

@pytest.mark.parametrize("now,expected", [
    (datetime(2024, 1, 2, 9, 0, 1), True),
    (datetime(2024, 1, 2, 9, 0, 0), False),
])
def test_is_missed_logic(sample_occurrence: TaskOccurrence, now: datetime, expected: bool) -> None:
    scheduler = TaskScheduler()
    assert scheduler.is_missed(sample_occurrence, now) is expected

def test_get_next_occurrence_with_recurrence(sample_task_def: TaskDefinition) -> None:
    scheduler = TaskScheduler()
    from_time = datetime(2024, 1, 2, 9, 0, 0)
    next_occ = scheduler.get_next_occurrence(sample_task_def, from_time)
    assert next_occ is not None
    assert sample_task_def.recurrence is not None
    assert next_occ.scheduled_for == from_time + sample_task_def.recurrence
    assert next_occ.task_id == sample_task_def.id

def test_get_next_occurrence_no_recurrence(sample_task_def: TaskDefinition) -> None:
    from dataclasses import replace
    scheduler = TaskScheduler()
    task = replace(sample_task_def, recurrence=None)
    assert scheduler.get_next_occurrence(task, datetime(2024, 1, 2, 9, 0, 0)) is None

@pytest.mark.parametrize("retries_remaining,state,expected", [
    (1, "missed", True),
    (2, "pending", True),
    (0, "missed", False),
    (0, "done", False),
    (1, "done", False),
])
def test_should_retry(retries_remaining: int, state: str, expected: bool) -> None:
    from typing import cast, Literal
    from addon.globalPlugins.planflow.task.task_model import TaskExecution
    execution = TaskExecution(
        occurrence_id="task1:123456",
        state=cast(Literal["pending", "done", "missed", "cancelled"], state),
        retries_remaining=retries_remaining,
        history=[],
    )
    scheduler = TaskScheduler()
    assert scheduler.should_retry(execution) is expected

def test_reschedule_retry_returns_new_occurrence(sample_occurrence: TaskOccurrence, sample_retry_policy: RetryPolicy) -> None:
    scheduler = TaskScheduler()
    now = datetime(2024, 1, 2, 10, 0, 0)
    new_occ = scheduler.reschedule_retry(sample_occurrence, sample_retry_policy, now)
    assert new_occ is not sample_occurrence
    assert new_occ.scheduled_for == now + sample_retry_policy.retry_interval
    assert new_occ.task_id == sample_occurrence.task_id
    assert new_occ.id.startswith(f"{sample_occurrence.task_id}:retry:")
