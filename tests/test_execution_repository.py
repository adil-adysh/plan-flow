"""Tests for ExecutionRepository: CRUD operations and roundtrip for TaskDefinition, TaskOccurrence, TaskExecution."""

import pytest
from datetime import datetime, timedelta
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from addon.globalPlugins.planflow.task.execution_repository import ExecutionRepository
from addon.globalPlugins.planflow.task.task_model import TaskDefinition, TaskOccurrence, TaskExecution, RetryPolicy, TaskEvent
from dataclasses import replace

def repo() -> ExecutionRepository:
@pytest.fixture
def repo() -> ExecutionRepository:
    return ExecutionRepository(TinyDB(storage=MemoryStorage))

def sample_task() -> TaskDefinition:
@pytest.fixture
def sample_task() -> TaskDefinition:
    return TaskDefinition(
        id="t1",
        title="Sample Task",
        description="desc",
        link=None,
        created_at=datetime(2025, 7, 10, 12, 0, 0),
        recurrence=timedelta(days=2),
        priority="high",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=3),
    )

def sample_occurrence(sample_task: TaskDefinition) -> TaskOccurrence:
@pytest.fixture
def sample_occurrence(sample_task: TaskDefinition) -> TaskOccurrence:
    return TaskOccurrence(
        id="o1",
        task_id=sample_task.id,
        scheduled_for=datetime(2025, 7, 12, 9, 0, 0),
        slot_name="morning",
        pinned_time=None,
    )

def sample_execution(sample_occurrence: TaskOccurrence) -> TaskExecution:
@pytest.fixture
def sample_execution(sample_occurrence: TaskOccurrence) -> TaskExecution:
    return TaskExecution(
        occurrence_id=sample_occurrence.id,
        state="pending",
        retries_remaining=2,
        history=[TaskEvent(event="triggered", timestamp=datetime(2025, 7, 12, 9, 0, 0))],
    )

def test_add_and_get_task(repo: ExecutionRepository, sample_task: TaskDefinition) -> None:
    repo.add_task(sample_task)
    fetched = repo.get_task(sample_task.id)
    assert fetched == sample_task

def test_list_tasks(repo: ExecutionRepository, sample_task: TaskDefinition) -> None:
    repo.add_task(sample_task)
    tasks = repo.list_tasks()
    assert len(tasks) == 1
    assert tasks[0] == sample_task

def test_add_and_list_occurrence(repo: ExecutionRepository, sample_occurrence: TaskOccurrence) -> None:
    repo.add_occurrence(sample_occurrence)
    occurrences = repo.list_occurrences()
    assert len(occurrences) == 1
    assert occurrences[0] == sample_occurrence

def test_add_and_list_execution(repo: ExecutionRepository, sample_execution: TaskExecution) -> None:
    repo.add_execution(sample_execution)
    executions = repo.list_executions()
    assert len(executions) == 1
    assert executions[0] == sample_execution

def test_task_idempotency(repo: ExecutionRepository, sample_task: TaskDefinition) -> None:
    repo.add_task(sample_task)
    # Overwrite with same id, different title
    updated = replace(sample_task, title="Updated")
    repo.add_task(updated)
    fetched = repo.get_task(sample_task.id)
    assert fetched is not None
    assert fetched.title == "Updated"

def test_occurrence_idempotency(repo: ExecutionRepository, sample_occurrence: TaskOccurrence) -> None:
    repo.add_occurrence(sample_occurrence)
    updated = replace(sample_occurrence, slot_name="afternoon")
    repo.add_occurrence(updated)
    occurrences = repo.list_occurrences()
    assert any(o.slot_name == "afternoon" for o in occurrences)

def test_execution_idempotency(repo: ExecutionRepository, sample_execution: TaskExecution) -> None:
    repo.add_execution(sample_execution)
    updated = replace(sample_execution, state="done")
    repo.add_execution(updated)
    executions = repo.list_executions()
    assert any(e.state == "done" for e in executions)

def test_empty_lists(repo: ExecutionRepository) -> None:
    assert repo.list_tasks() == []
    assert repo.list_occurrences() == []
    assert repo.list_executions() == []
