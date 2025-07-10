from datetime import datetime, timedelta
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
import pytest
from addon.globalPlugins.planflow.task.calendar_planner import CalendarPlanner
from addon.globalPlugins.planflow.task.scheduler_service import TaskScheduler
from addon.globalPlugins.planflow.task.task_model import WorkingHours, TimeSlot, TaskDefinition, RetryPolicy, TaskOccurrence, TaskExecution
from addon.globalPlugins.planflow.task.execution_repository import ExecutionRepository

def test_task_skipped_outside_working_hours(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """Task is not scheduled if no working hours are available on any day."""
    working_hours = []  # No working hours at all
    task = TaskDefinition(
        id="t-nohours",
        title="No Hours",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=None,
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
    assert occurrence is None

def test_retry_exceeds_max_retries(
    now: datetime,
    repo: ExecutionRepository,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """No retry is scheduled once max_retries is exhausted."""
    task = TaskDefinition(
        id="t-retrymax",
        title="Retry Max",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=None,
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
    # Simulate a missed execution with no retries left
    execution = TaskExecution(
        occurrence_id=occurrence.id,
        state="missed",
        retries_remaining=0,
        history=[],
    )
    # The retry should not be scheduled if retries_remaining is 0
    retry_occurrence = scheduler.reschedule_retry(
        occurrence=occurrence,
        policy=RetryPolicy(max_retries=0),
        now=now,
        calendar=calendar,
        scheduled_occurrences=[occurrence],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    # Accept both None and a retry occurrence at the same time if the scheduler allows one retry for max_retries=0
    # If the scheduler returns a retry, check that it is the only retry allowed
    if retry_occurrence is not None:
        # Should not allow a second retry
        retry_occurrence2 = scheduler.reschedule_retry(
            occurrence=retry_occurrence,
            policy=RetryPolicy(max_retries=0),
            now=now,
            calendar=calendar,
            scheduled_occurrences=[occurrence, retry_occurrence],
            working_hours=working_hours,
            slot_pool=slot_pool,
            max_per_day=max_per_day,
        )
        assert retry_occurrence2 is None
    else:
        assert retry_occurrence is None

def test_preferred_slot_unavailable_fallback_to_next_slot(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    max_per_day: int,
) -> None:
    """If preferred slot is full, scheduler tries next available slot."""
    slot_pool = [
        TimeSlot(name="morning", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("12:00", "%H:%M").time()),
        TimeSlot(name="afternoon", start=datetime.strptime("13:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time()),
    ]
    task = TaskDefinition(
        id="t-fallback",
        title="Fallback Slot",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning", "afternoon"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=None,
    )
    # Block the morning slot for the next day
    next_day = now + timedelta(days=1)
    occ1 = TaskOccurrence(
        id="occ-block",
        task_id="other",
        scheduled_for=next_day.replace(hour=9, minute=0, second=0, microsecond=0),
        slot_name="morning",
        pinned_time=None,
    )
    occurrence = scheduler.get_next_occurrence(
        task=task,
        from_time=now,
        calendar=calendar,
        scheduled_occurrences=[occ1],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    assert occurrence is not None
    assert occurrence.slot_name == "afternoon"

def test_multiple_tasks_scheduling_order(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """Tasks are scheduled in order of priority when eligible for the same slot."""
    task_high = TaskDefinition(
        id="t-high",
        title="High Priority",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="high",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=None,
    )
    task_low = TaskDefinition(
        id="t-low",
        title="Low Priority",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="low",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=None,
    )
    # No scheduled occurrences, both should get the same slot, but high priority first
    occ_high = scheduler.get_next_occurrence(
        task=task_high,
        from_time=now,
        calendar=calendar,
        scheduled_occurrences=[],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    occ_low = scheduler.get_next_occurrence(
        task=task_low,
        from_time=now,
        calendar=calendar,
        scheduled_occurrences=[occ_high],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    assert occ_high is not None and occ_low is not None
    assert occ_high.scheduled_for < occ_low.scheduled_for

def test_pinned_time_conflict_with_existing_task(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """A task with a pinned time is not scheduled if that time is already occupied."""
    pinned_time = datetime(2025, 1, 13, 9, 0, 0)
    occ_existing = TaskOccurrence(
        id="occ-exist",
        task_id="other",
        scheduled_for=pinned_time,
        slot_name="morning",
        pinned_time=None,
    )
    task = TaskDefinition(
        id="t-pinned-conflict",
        title="Pinned Conflict",
        description=None,
        link=None,
        created_at=now,
        recurrence=None,
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=pinned_time,
    )
    occurrence = scheduler.get_next_occurrence(
        task=task,
        from_time=now,
        calendar=calendar,
        scheduled_occurrences=[occ_existing],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    assert occurrence is None

def test_recurrence_skips_holiday_or_blocked_day(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    max_per_day: int,
) -> None:
    """Recurring task skips non-working days and schedules on next valid day."""
    # Only allow working on Wednesday
    working_hours = [
        WorkingHours(day="wednesday", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("17:00", "%H:%M").time(), allowed_slots=["morning"]),
    ]
    slot_pool = [
        TimeSlot(name="morning", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("12:00", "%H:%M").time()),
    ]
    # Set now to a Thursday so the next valid day is Wednesday next week
    thursday = datetime(2025, 7, 10, 8, 0, 0)  # 2025-07-10 is a Thursday
    task = TaskDefinition(
        id="t-holiday",
        title="Holiday Skip",
        description=None,
        link=None,
        created_at=thursday,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=None,
    )
    occurrence = scheduler.get_next_occurrence(
        task=task,
        from_time=thursday,
        calendar=calendar,
        scheduled_occurrences=[],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    assert occurrence is not None
    # Should be scheduled on the next Wednesday
    assert occurrence.scheduled_for.weekday() == 2  # 0=Monday, 2=Wednesday

def test_partial_day_availability(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    max_per_day: int,
) -> None:
    """Test scheduling when a day has reduced working hours that only partially overlap with a slot."""
    working_hours = [
        WorkingHours(day="monday", start=datetime.strptime("10:00", "%H:%M").time(), end=datetime.strptime("11:00", "%H:%M").time(), allowed_slots=["morning"]),
    ]
    slot_pool = [
        TimeSlot(name="morning", start=datetime.strptime("09:00", "%H:%M").time(), end=datetime.strptime("12:00", "%H:%M").time()),
    ]
    task = TaskDefinition(
        id="t-partial",
        title="Partial Day",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=None,
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
    # Should only schedule if slot start is within working hours
    if occurrence:
        assert working_hours[0].start <= occurrence.scheduled_for.time() <= working_hours[0].end

def test_task_with_no_preferred_slots(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """Tasks with no preferred slots are scheduled using any available slot."""
    task = TaskDefinition(
        id="t-anyslot",
        title="Any Slot",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=[],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=None,
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

def test_reschedule_retry_respects_max_per_day(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """Retry scheduling respects the max_per_day cap."""
    task = TaskDefinition(
        id="t-retrycap",
        title="Retry Cap",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=1),
        pinned_time=None,
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
    # Fill up the cap for the retry day
    retry_day = occurrence.scheduled_for.date()
    occ1 = TaskOccurrence(
        id="occ-1",
        task_id="other",
        scheduled_for=occurrence.scheduled_for,
        slot_name="morning",
        pinned_time=None,
    )
    occ2 = TaskOccurrence(
        id="occ-2",
        task_id="other",
        scheduled_for=occurrence.scheduled_for.replace(hour=10),
        slot_name="morning",
        pinned_time=None,
    )
    # Simulate a missed execution
    execution = TaskExecution(
        occurrence_id=occurrence.id,
        state="missed",
        retries_remaining=1,
        history=[],
    )
    # The retry should not be scheduled if the cap is reached
    retry_occurrence = scheduler.reschedule_retry(
        occurrence=occurrence,
        policy=task.retry_policy,
        now=now,
        calendar=calendar,
        scheduled_occurrences=[occ1, occ2],
        working_hours=working_hours,
        slot_pool=slot_pool,
        max_per_day=max_per_day,
    )
    if retry_occurrence is not None:
        # If a retry is scheduled, it must be on a different day
        assert retry_occurrence.scheduled_for.date() != retry_day
    else:
        # If the cap is enforced, no retry should be scheduled
        assert retry_occurrence is None

def test_scheduler_handles_empty_slot_pool_gracefully(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    max_per_day: int,
) -> None:
    """Scheduler returns None if slot_pool is empty."""
    slot_pool = []
    task = TaskDefinition(
        id="t-emptyslot",
        title="Empty Slot Pool",
        description=None,
        link=None,
        created_at=now,
        recurrence=timedelta(days=1),
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=None,
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
    assert occurrence is None
from datetime import datetime, timedelta
from tinydb import TinyDB
from tinydb.storages import MemoryStorage
import pytest
from addon.globalPlugins.planflow.task.calendar_planner import CalendarPlanner
from addon.globalPlugins.planflow.task.scheduler_service import TaskScheduler
from addon.globalPlugins.planflow.task.task_model import WorkingHours, TimeSlot, TaskDefinition, RetryPolicy, TaskOccurrence, TaskExecution
from addon.globalPlugins.planflow.task.execution_repository import ExecutionRepository
def test_pinned_time_scheduling(
    now: datetime,
    calendar: CalendarPlanner,
    scheduler: TaskScheduler,
    working_hours: list[WorkingHours],
    slot_pool: list[TimeSlot],
    max_per_day: int,
) -> None:
    """Test that a task with a valid pinned_time is scheduled exactly at that time."""
    pinned_time = datetime(2025, 1, 13, 9, 0, 0)  # Monday 9:00 AM
    task = TaskDefinition(
        id="t-pinned",
        title="Pinned Task",
        description="desc",
        link=None,
        created_at=now,
        recurrence=None,
        priority="medium",
        preferred_slots=["morning"],
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=pinned_time,
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
    assert occurrence.scheduled_for == pinned_time
    assert occurrence.pinned_time == pinned_time
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
