"""Integration tests for SmartSchedulerController."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from addon.globalPlugins.planflow.task.smart_scheduler_controller import SmartSchedulerController
from addon.globalPlugins.planflow.task.task_model import TaskOccurrence, TaskDefinition, RetryPolicy

@pytest.fixture
def sample_task():
	return TaskDefinition(
		id="task1",
		title="Test Task",
		description=None,
		link=None,
		created_at=datetime(2024, 1, 1),
		recurrence=timedelta(days=1),
		priority="medium",
		preferred_slots=[],
		retry_policy=RetryPolicy(max_retries=1),
		pinned_time=None,
	)

@pytest.fixture
def sample_occurrence(sample_task):
	return TaskOccurrence(
		id="occ1",
		task_id=sample_task.id,
		scheduled_for=datetime.now() + timedelta(hours=1),
		slot_name=None,
		pinned_time=None,
	)

@pytest.fixture
def controller_and_mocks(sample_task, sample_occurrence):
	def now_fn() -> datetime:
		return datetime.now()
	smart_scheduler = MagicMock()
	repo = MagicMock()
	scheduler = MagicMock()
	recovery = MagicMock()
	calendar = MagicMock()
	repo.list_occurrences.return_value = [sample_occurrence]
	repo.list_tasks.return_value = [sample_task]
	repo.list_executions.return_value = []
	controller = SmartSchedulerController(
		smart_scheduler, repo, scheduler, recovery, calendar, now_fn
	)
	return controller, smart_scheduler, repo, scheduler, recovery, calendar

def test_start_schedules_and_recovers(controller_and_mocks):
	controller, smart_scheduler, *_ = controller_and_mocks
	controller.start()
	smart_scheduler.start.assert_called_once()

def test_mark_done_creates_execution_and_schedules_retry(controller_and_mocks, sample_occurrence):
	controller, smart_scheduler, repo, scheduler, *_ = controller_and_mocks
	scheduler.reschedule_retry.return_value = sample_occurrence
	controller.mark_done(sample_occurrence.id)
	smart_scheduler.schedule_occurrence.assert_called_with(sample_occurrence)


def test_mark_done_falls_back_to_recurrence(controller_and_mocks, sample_occurrence, sample_task):
	controller, smart_scheduler, repo, scheduler, *_ = controller_and_mocks
	scheduler.reschedule_retry.return_value = None
	scheduler.get_next_occurrence.return_value = sample_occurrence
	controller.mark_done(sample_occurrence.id)
	smart_scheduler.schedule_occurrence.assert_called_with(sample_occurrence)


def test_retry_occurrence_returns_occurrence_if_valid(controller_and_mocks, sample_occurrence):
	controller, smart_scheduler, repo, scheduler, *_ = controller_and_mocks
	scheduler.reschedule_retry.return_value = sample_occurrence
	result = controller.retry_occurrence(sample_occurrence.id)
	assert result == sample_occurrence
	smart_scheduler.schedule_occurrence.assert_called_with(sample_occurrence)


def test_retry_occurrence_returns_none_if_retry_exhausted(controller_and_mocks, sample_occurrence):
	controller, smart_scheduler, repo, scheduler, *_ = controller_and_mocks
	scheduler.reschedule_retry.return_value = None
	result = controller.retry_occurrence(sample_occurrence.id)
	assert result is None


def test_resume_triggers_schedule_all(controller_and_mocks):
	controller, smart_scheduler, *_ = controller_and_mocks
	controller.resume()
	smart_scheduler.start.assert_called_once()


def test_get_scheduled_occurrences_returns_expected_set(controller_and_mocks, sample_occurrence):
	controller, smart_scheduler, *_ = controller_and_mocks
	smart_scheduler.get_scheduled_occurrences.return_value = [sample_occurrence]
	result = controller.get_scheduled_occurrences()
	assert result == [sample_occurrence]


def test_recover_missed_tasks_delegates_to_recovery_service(controller_and_mocks, sample_occurrence):
	controller, smart_scheduler, repo, scheduler, recovery, *_ = controller_and_mocks
	recovery.recover_missed_occurrences.return_value = [sample_occurrence]
	result = controller.recover_missed_tasks()
	assert result == [sample_occurrence]
	smart_scheduler.schedule_occurrence.assert_called_with(sample_occurrence)


def test_invalid_occurrence_id_raises(controller_and_mocks):
	controller, *_ = controller_and_mocks
	with pytest.raises(ValueError):
		controller.mark_done("invalid_id")
	with pytest.raises(ValueError):
		controller.retry_occurrence("invalid_id")
