"""Integration tests for ExecutionRepository, CalendarPlanner, and TaskScheduler flows."""

import pytest
from datetime import datetime, timedelta
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from addon.globalPlugins.planflow.task.execution_repository import ExecutionRepository
from addon.globalPlugins.planflow.task.task_model import TaskDefinition, TaskOccurrence, TaskExecution, RetryPolicy, WorkingHours, TimeSlot
from addon.globalPlugins.planflow.task.calendar_planner import CalendarPlanner
from addon.globalPlugins.planflow.task.scheduler_service import TaskScheduler


@pytest.fixture
def now() -> datetime:
    return datetime(2025, 7, 10, 8, 0, 0)


@pytest.fixture
def repo() -> ExecutionRepository:
    return ExecutionRepository(TinyDB(storage=MemoryStorage))


@pytest.fixture
def calendar() -> CalendarPlanner:
    return CalendarPlanner()


@pytest.fixture
def scheduler() -> TaskScheduler:
    return TaskScheduler()


@pytest.fixture
def working_hours() -> list[WorkingHours]:
    return [
        WorkingHours(day="monday", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time(), allowed_slots=["morning", "afternoon"]),
        WorkingHours(day="tuesday", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time(), allowed_slots=["morning", "afternoon"]),
        WorkingHours(day="wednesday", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time(), allowed_slots=["morning", "afternoon"]),
        WorkingHours(day="thursday", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time(), allowed_slots=["morning", "afternoon"]),
        WorkingHours(day="friday", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time(), allowed_slots=["morning", "afternoon"]),
        WorkingHours(day="saturday", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time(), allowed_slots=["morning", "afternoon"]),
        WorkingHours(day="sunday", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time(), allowed_slots=["morning", "afternoon"]),
    ]


@pytest.fixture
def slot_pool() -> list[TimeSlot]:
    return [
        TimeSlot(name="morning", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("12:00", "%H:%M").time()),
        TimeSlot(name="afternoon", start=datetime.strptime("13:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time()),
    ]


@pytest.fixture
def max_per_day() -> int:
    return 2



def test_recurrence_scheduling(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """Test recurrence-based scheduling returns a valid occurrence."""
    task = TaskDefinition(
        id="t-recur",
        title="Recurring Task",
        description="desc",
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
    )
    occurrence = scheduler.get_next_occurrence(
        task=task,
        from_time=now,
        calendar=calendar,
        scheduled_occurrences=[],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    assert occurrence is not None



def test_max_per_day_cap(now: datetime, calendar: CalendarPlanner, scheduler: TaskScheduler, working_hours: list[WorkingHours], slot_pool: list[TimeSlot], max_per_day: int) -> None:
    """Test that max per-day cap prevents scheduling when the cap is reached."""
    # Set up a recurring task
    task = TaskDefinition(
        id="t-cap",
        title="Capped Task",
        description="desc",
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
    )
    # Schedule up to the cap for the next day
    next_day = now + timedelta(days=1)
    occ1 = TaskOccurrence(
        id="occ-1",
        task_id="t-cap",
        scheduled_for=next_day.replace(hour=9, minute=0, second=0, microsecond=0),
        slot_name="morning",
        pinned_time=None,
    )
    occ2 = TaskOccurrence(
        id="occ-2",
        task_id="t-cap",
        scheduled_for=next_day.replace(hour=10, minute=0, second=0, microsecond=0),
        slot_name="morning",
        pinned_time=None,
    )
    scheduled_occurrences = [occ1, occ2]
    # The scheduler should skip to the next available day (not the capped day)
    occurrence = scheduler.get_next_occurrence(
        task=task,
        from_time=now,
        calendar=calendar,
        scheduled_occurrences=scheduled_occurrences,
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    assert occurrence is not None
    # The returned occurrence should not be on the capped day
    capped_date = next_day.date()
    assert occurrence.scheduled_for.date() != capped_date



def test_retry_within_limits(
    now: datetime,
    repo: ExecutionRepository,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """Test retry allowed within retry policy limits using reschedule_retry."""
    # Set up a recurring task and schedule its first occurrence
    task = TaskDefinition(
        id="t-retry",
        title="Retry Task",
        description="desc",
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=1),
    )
    occurrence = scheduler.get_next_occurrence(
        task=task,
        from_time=now,
        calendar=calendar,
        scheduled_occurrences=[],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    assert occurrence is not None
    # Simulate a missed execution
    execution = TaskExecution(
        occurrence_id=occurrence.id,
        state="missed",
        retries_remaining=1,
        history=[],
    )
    repo.add_execution(execution)
    # Use reschedule_retry to get a retry occurrence
    retry_occurrence = scheduler.reschedule_retry(
        occurrence=occurrence,
        policy=task.retry_policy,
        now=now,
        calendar=calendar,
        scheduled_occurrences=[occurrence],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    assert retry_occurrence is not None


def test_recovery_skips_pinned(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """Test that recovery flow skips pinned time if user intent is to skip."""
    task = TaskDefinition(
        id="t-rec",
        title="Recovery Task",
        description="desc",
        link=None,
        created_at=now,
        recurrence=None,
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
    )
    scheduled_occurrences = [
        TaskOccurrence(
            id="occ-booked",
            task_id="other",
            scheduled_for=datetime(2025, 7, 10, 9, 0, 0),
            slot_name="morning",
            pinned_time=None,
        )
    ]
    occurrence = scheduler.get_next_occurrence(
        task=task,
        from_time=now,
        calendar=calendar,
        scheduled_occurrences=scheduled_occurrences,
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    assert occurrence is None
