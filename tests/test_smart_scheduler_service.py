"""Unit tests for SmartSchedulerService in PlanFlow.

Covers scheduling, missed task detection, retry, recurrence, pause/resume, and slot validation.
"""

import threading
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from collections.abc import Callable
import pytest

from addon.globalPlugins.planflow.task.smart_scheduler_service import SmartSchedulerService
from addon.globalPlugins.planflow.task.task_model import (
    TaskOccurrence,
    TaskDefinition,
    RetryPolicy,
    TaskExecution,
)

# --- Fixtures ---


@pytest.fixture
def now_fn() -> Callable[[], datetime]:
    return lambda: datetime(2025, 1, 1, 9, 0, 0)


@pytest.fixture
def sample_occ(now_fn: Callable[[], datetime]) -> TaskOccurrence:
    return TaskOccurrence(
        id="occ-1",
        task_id="task-1",
        scheduled_for=now_fn() + timedelta(minutes=5),
        slot_name=None,
        pinned_time=None,
    )


@pytest.fixture
def executed_occ(now_fn: Callable[[], datetime]) -> TaskOccurrence:
    return TaskOccurrence(
        id="occ-2",
        task_id="task-2",
        scheduled_for=now_fn() - timedelta(minutes=10),
        slot_name=None,
        pinned_time=None,
    )


@pytest.fixture
def execution_repo() -> MagicMock:
    repo = MagicMock()
    repo.list_occurrences.return_value = []
    repo.list_executions.return_value = []
    repo.get_task.return_value = None
    return repo


@pytest.fixture
def scheduler() -> MagicMock:
    return MagicMock()


@pytest.fixture
def calendar() -> MagicMock:
    cal = MagicMock()
    cal.is_slot_available.return_value = True
    return cal


@pytest.fixture
def recovery() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(
    execution_repo: MagicMock,
    scheduler: MagicMock,
    calendar: MagicMock,
    recovery: MagicMock,
    now_fn: Callable[[], datetime],
) -> SmartSchedulerService:
    return SmartSchedulerService(
        execution_repo=execution_repo,
        scheduler=scheduler,
        calendar=calendar,
        recovery=recovery,
        now_fn=now_fn,
    )


# --- Test Cases ---


def test_task_due_immediately(
    service: SmartSchedulerService,
    sample_occ: TaskOccurrence,
    now_fn: Callable[[], datetime],
) -> None:
    occ = TaskOccurrence(
        id=sample_occ.id,
        task_id=sample_occ.task_id,
        scheduled_for=now_fn() - timedelta(seconds=1),
        slot_name=sample_occ.slot_name,
        pinned_time=sample_occ.pinned_time,
    )
    service._on_trigger = MagicMock()
    service.schedule_occurrence(occ)
    service._on_trigger.assert_called_once_with(occ)


def test_future_task_scheduled(
    service: SmartSchedulerService,
    sample_occ: TaskOccurrence,
) -> None:
    service._on_trigger = MagicMock()
    service.schedule_occurrence(sample_occ)
    assert sample_occ.id in service._timers
    assert isinstance(service._timers[sample_occ.id], threading.Timer)
    assert service._timers[sample_occ.id].daemon is True


def test_task_already_executed(
    service: SmartSchedulerService,
    sample_occ: TaskOccurrence,
    execution_repo: MagicMock,
) -> None:
    execution_repo.list_executions.return_value = [
        TaskExecution(occurrence_id=sample_occ.id, state="done", retries_remaining=0)
    ]
    service.schedule_occurrence(sample_occ)
    assert sample_occ.id not in service._timers


def test_slot_invalid_skipped(
    service: SmartSchedulerService,
    sample_occ: TaskOccurrence,
    calendar: MagicMock,
) -> None:
    calendar.is_slot_available.return_value = False
    service.schedule_occurrence(sample_occ)
    assert sample_occ.id not in service._timers


def test_task_missed_within_grace(
    service: SmartSchedulerService,
    sample_occ: TaskOccurrence,
    execution_repo: MagicMock,
    now_fn: Callable[[], datetime],
) -> None:
    occ = TaskOccurrence(
        id=sample_occ.id,
        task_id=sample_occ.task_id,
        scheduled_for=now_fn() - timedelta(seconds=10),
        slot_name=sample_occ.slot_name,
        pinned_time=sample_occ.pinned_time,
    )
    execution_repo.list_occurrences.return_value = [occ]
    execution_repo.list_executions.return_value = []
    service._on_trigger = MagicMock()
    service.check_for_missed_tasks()
    service._on_trigger.assert_called_once_with(occ)


def test_task_missed_beyond_grace(
    service: SmartSchedulerService,
    sample_occ: TaskOccurrence,
    execution_repo: MagicMock,
    now_fn: Callable[[], datetime],
) -> None:
    occ = TaskOccurrence(
        id=sample_occ.id,
        task_id=sample_occ.task_id,
        scheduled_for=now_fn() - timedelta(seconds=40),
        slot_name=sample_occ.slot_name,
        pinned_time=sample_occ.pinned_time,
    )
    execution_repo.list_occurrences.return_value = [occ]
    execution_repo.list_executions.return_value = []
    service._trigger_recovery = MagicMock()
    service.check_for_missed_tasks()
    service._trigger_recovery.assert_called_once_with(occ)


def test_retry_schedules_new_occurrence(
    service: SmartSchedulerService,
    sample_occ: TaskOccurrence,
    scheduler: MagicMock,
    execution_repo: MagicMock,
) -> None:
    policy = RetryPolicy(max_retries=1)

    retry_occ = TaskOccurrence(
        id="occ-retry",
        task_id=sample_occ.task_id,
        scheduled_for=sample_occ.scheduled_for,
        slot_name=sample_occ.slot_name,
        pinned_time=sample_occ.pinned_time,
    )
    scheduler.reschedule_retry.return_value = retry_occ
    execution_repo.get_task.return_value = TaskDefinition(
        id=sample_occ.task_id,
        title="Test",
        description=None,
        link=None,
        created_at=datetime(2025, 1, 1, 8, 0, 0),
        recurrence=None,
        preferred_slots=[],
        priority="medium",
        retry_policy=policy,
        pinned_time=None,
    )
    service.schedule_occurrence = MagicMock()
    service._on_trigger(sample_occ)
    service.schedule_occurrence.assert_called_with(retry_occ)


def test_recurrence_schedules_new_occurrence(
    service: SmartSchedulerService,
    sample_occ: TaskOccurrence,
    scheduler: MagicMock,
    execution_repo: MagicMock,
) -> None:
    scheduler.reschedule_retry.return_value = None
    recurrence = timedelta(days=1)

    task = TaskDefinition(
        id=sample_occ.task_id,
        title="Test",
        description=None,
        link=None,
        created_at=datetime(2025, 1, 1, 8, 0, 0),
        recurrence=recurrence,
        preferred_slots=[],
        priority="medium",
        retry_policy=RetryPolicy(max_retries=1),
        pinned_time=None,
    )
    execution_repo.get_task.return_value = task
    scheduler.get_next_occurrence.return_value = sample_occ
    service.schedule_occurrence = MagicMock()
    service._on_trigger(sample_occ)
    service.schedule_occurrence.assert_called_with(sample_occ)


def test_pause_prevents_timers(
    service: SmartSchedulerService,
    sample_occ: TaskOccurrence,
) -> None:
    service.pause()
    service.schedule_occurrence(sample_occ)
    assert sample_occ.id not in service._timers


def test_resume_restarts_scheduling(
    service: SmartSchedulerService,
    execution_repo: MagicMock,
    sample_occ: TaskOccurrence,
) -> None:
    execution_repo.list_occurrences.return_value = [sample_occ]
    execution_repo.list_executions.return_value = []
    service.pause()
    service.start()
    assert sample_occ.id in service._timers
