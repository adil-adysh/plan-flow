"""Tests for ExecutionRepository: CRUD operations and roundtrip for TaskDefinition, TaskOccurrence, TaskExecution."""

import pytest
from datetime import datetime, timedelta
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from addon.globalPlugins.planflow.task.execution_repository import ExecutionRepository
from addon.globalPlugins.planflow.task.task_model import TaskDefinition, TaskOccurrence, TaskExecution, RetryPolicy, TaskEvent
from dataclasses import replace


@pytest.fixture
def repo() -> ExecutionRepository:
    return ExecutionRepository(TinyDB(storage=MemoryStorage))


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


@pytest.fixture
def sample_occurrence(sample_task: TaskDefinition) -> TaskOccurrence:
    return TaskOccurrence(
        id="o1",
        task_id=sample_task.id,
        scheduled_for=datetime(2025, 7, 12, 9, 0, 0),
        slot_name="morning",
        pinned_time=None,
    )


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

def test_delete_task_and_related_removes_all(repo: ExecutionRepository, sample_task: TaskDefinition, sample_occurrence: TaskOccurrence, sample_execution: TaskExecution) -> None:
    repo.add_task(sample_task)
    repo.add_occurrence(sample_occurrence)
    repo.add_execution(sample_execution)
    # Sanity check: all present
    assert repo.get_task(sample_task.id) is not None
    assert any(o.id == sample_occurrence.id for o in repo.list_occurrences())
    assert any(e.occurrence_id == sample_occurrence.id for e in repo.list_executions())
    # Delete
    repo.delete_task_and_related(sample_task.id)
    # All gone
    assert repo.get_task(sample_task.id) is None
    assert not any(o.task_id == sample_task.id for o in repo.list_occurrences())
    assert not any(e.occurrence_id == sample_occurrence.id for e in repo.list_executions())

def test_delete_task_and_related_only_affects_target(repo: ExecutionRepository, sample_task: TaskDefinition, sample_occurrence: TaskOccurrence, sample_execution: TaskExecution) -> None:
    # Add a second unrelated task/occ/execution
    other_task = replace(sample_task, id="t2", title="Other")
    other_occ = replace(sample_occurrence, id="o2", task_id="t2")
    other_exec = replace(sample_execution, occurrence_id="o2")
    repo.add_task(sample_task)
    repo.add_occurrence(sample_occurrence)
    repo.add_execution(sample_execution)
    repo.add_task(other_task)
    repo.add_occurrence(other_occ)
    repo.add_execution(other_exec)
    # Delete first task
    repo.delete_task_and_related(sample_task.id)
    # First gone, second remains
    assert repo.get_task(sample_task.id) is None
    assert repo.get_task("t2") is not None
    assert not any(o.task_id == sample_task.id for o in repo.list_occurrences())
    assert any(o.task_id == "t2" for o in repo.list_occurrences())
    assert not any(e.occurrence_id == sample_occurrence.id for e in repo.list_executions())
    assert any(e.occurrence_id == "o2" for e in repo.list_executions())
