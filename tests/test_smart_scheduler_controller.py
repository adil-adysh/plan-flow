"""Unit tests for SmartSchedulerController (core logic, no integration)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from addon.globalPlugins.planflow.task.smart_scheduler_controller import SmartSchedulerController
from addon.globalPlugins.planflow.task.task_model import TaskOccurrence, TaskDefinition, RetryPolicy

@pytest.fixture
def now() -> datetime:
	return datetime(2025, 1, 1, 12, 0, 0)

@pytest.fixture
def sample_task() -> TaskDefinition:
	return TaskDefinition(
		id="t1",
		title="UnitTest",
		description=None,
		link=None,
		created_at=datetime(2024, 1, 1),
		recurrence=timedelta(days=1),
		priority="medium",
		preferred_slots=[],
		retry_policy=RetryPolicy(max_retries=2),
		pinned_time=None,
	)

@pytest.fixture
def sample_occurrence(sample_task: TaskDefinition, now: datetime) -> TaskOccurrence:
	return TaskOccurrence(
		id="o1",
		task_id=sample_task.id,
		scheduled_for=now + timedelta(hours=1),
		slot_name=None,
		pinned_time=None,
	)

@pytest.fixture
def controller(sample_task: TaskDefinition, sample_occurrence: TaskOccurrence, now: datetime) -> SmartSchedulerController:
	smart_scheduler = MagicMock()
	repo = MagicMock()
	scheduler = MagicMock()
	recovery = MagicMock()
	calendar = MagicMock()
	def now_fn() -> datetime:
		return now
	repo.list_occurrences.return_value = [sample_occurrence]
	repo.list_tasks.return_value = [sample_task]
	repo.list_executions.return_value = []
	return SmartSchedulerController(
		smart_scheduler, repo, scheduler, recovery, calendar, now_fn
	)

def test_already_done_true_when_execution_exists(controller: SmartSchedulerController, sample_occurrence: TaskOccurrence) -> None:
	controller._repo.list_executions.return_value = [MagicMock(occurrence_id=sample_occurrence.id, state="done")]
	assert controller._already_done(sample_occurrence.id)

def test_already_done_false_when_no_execution(controller: SmartSchedulerController, sample_occurrence: TaskOccurrence) -> None:
	controller._repo.list_executions.return_value = []
	assert not controller._already_done(sample_occurrence.id)

def test_get_occurrence_raises_for_invalid(controller: SmartSchedulerController) -> None:
	controller._repo.list_occurrences.return_value = []
	with pytest.raises(ValueError):
		controller._get_occurrence("badid")

def test_get_task_raises_for_invalid(controller: SmartSchedulerController) -> None:
	controller._repo.list_tasks.return_value = []
	with pytest.raises(ValueError):
		controller._get_task("badid")
