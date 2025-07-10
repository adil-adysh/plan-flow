
"""
Tests for CalendarPlanner: working hours, slot, per-day cap, slot preference, holidays, and edge cases.
"""

import pytest
from datetime import datetime, time
from addon.globalPlugins.planflow.task.calendar_planner import CalendarPlanner
from addon.globalPlugins.planflow.task.task_model import TaskOccurrence, TimeSlot, WorkingHours

def make_occurrence(dt: datetime, slot_name: str | None = None) -> TaskOccurrence:
    return TaskOccurrence(id="occ-"+dt.isoformat(), task_id="t1", scheduled_for=dt, slot_name=slot_name)

from typing import Literal

def wh(day: Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"], start: time, end: time, allowed_slots: tuple[str, ...] = ()) -> WorkingHours:
    return WorkingHours(day=day, start=start, end=end, allowed_slots=list(allowed_slots))

def ts(name: str, start: time, end: time) -> TimeSlot:
    return TimeSlot(name=name, start=start, end=end)

@pytest.fixture
def planner() -> CalendarPlanner:
    return CalendarPlanner()

@pytest.fixture
def working_hours() -> list[WorkingHours]:
    return [
        wh("monday", time(8, 0), time(18, 0), ("morning", "afternoon")),
        wh("tuesday", time(8, 0), time(18, 0), ("morning", "afternoon")),
        wh("wednesday", time(8, 0), time(18, 0), ("morning", "afternoon")),
        wh("thursday", time(8, 0), time(18, 0), ("morning", "afternoon")),
        wh("friday", time(8, 0), time(18, 0), ("morning", "afternoon")),
    ]

@pytest.fixture
def slot_pool() -> list[TimeSlot]:
    return [
        ts("morning", time(9, 0), time(10, 0)),
        ts("afternoon", time(15, 0), time(16, 0)),
        ts("evening", time(20, 0), time(21, 0)),
    ]

@pytest.mark.parametrize("proposed_time,occurrences,expected", [
    # Available slot within working hours and allowed slot
    (datetime(2025, 7, 7, 9, 0), [], True),
    # Not in working hours
    (datetime(2025, 7, 7, 7, 0), [], False),
    # Not in allowed slot (slot name not in allowed_slots)
    (datetime(2025, 7, 7, 20, 0), [], False),
    # Day filled
    (datetime(2025, 7, 7, 9, 0), [make_occurrence(datetime(2025, 7, 7, 8, 0)), make_occurrence(datetime(2025, 7, 7, 15, 0))], False),
    # Time collision
    (datetime(2025, 7, 7, 9, 0), [make_occurrence(datetime(2025, 7, 7, 9, 0))], False),
    # Holiday (no working hours)
    (datetime(2025, 7, 6, 9, 0), [], False),
])
def test_is_slot_available_cases(
    proposed_time: datetime,
    occurrences: list[TaskOccurrence],
    expected: bool,
    planner: CalendarPlanner,
    working_hours: list[WorkingHours],
) -> None:
    # Use slot_pool fixture for slot validation
    # (no unused imports)
    import inspect
    # Try to get slot_pool from the test context if available
    frame = inspect.currentframe()
    slot_pool = None
    while frame:
        if 'slot_pool' in frame.f_locals:
            slot_pool = frame.f_locals['slot_pool']
            break
        frame = frame.f_back
    if slot_pool is None:
        # fallback: create default slot_pool
        slot_pool = [
            ts("morning", time(9, 0), time(10, 0)),
            ts("afternoon", time(15, 0), time(16, 0)),
            ts("evening", time(20, 0), time(21, 0)),
        ]
    result = planner.is_slot_available(
        proposed_time=proposed_time,
        scheduled_occurrences=occurrences,
        working_hours=working_hours,
        max_per_day=2,
        slot_pool=slot_pool
    )
    assert result is expected

def test_next_available_slot_basic(
    planner: CalendarPlanner,
    slot_pool: list[TimeSlot],
    working_hours: list[WorkingHours],
) -> None:
    # No scheduled tasks, should return first slot on Monday after 'after'
    after = datetime(2025, 7, 6, 8, 0)  # Sunday
    result = planner.next_available_slot(
        after=after,
        slot_pool=slot_pool,
        scheduled_occurrences=[],
        working_hours=working_hours,
        max_per_day=2
    )
    assert result == datetime(2025, 7, 7, 9, 0)

def test_next_available_slot_day_filled(
    planner: CalendarPlanner,
    slot_pool: list[TimeSlot],
    working_hours: list[WorkingHours],
) -> None:
    # Monday is filled, should return Tuesday morning
    after = datetime(2025, 7, 6, 8, 0)
    occurrences = [
        make_occurrence(datetime(2025, 7, 7, 9, 0)),
        make_occurrence(datetime(2025, 7, 7, 15, 0)),
    ]
    result = planner.next_available_slot(
        after=after,
        slot_pool=slot_pool,
        scheduled_occurrences=occurrences,
        working_hours=working_hours,
        max_per_day=2
    )
    assert result == datetime(2025, 7, 8, 9, 0)

def test_next_available_slot_skips_holiday(
    planner: CalendarPlanner,
    slot_pool: list[TimeSlot],
    working_hours: list[WorkingHours],
) -> None:
    # Sunday is a holiday (no working hours), should skip to Monday
    after = datetime(2025, 7, 6, 7, 0)
    result = planner.next_available_slot(
        after=after,
        slot_pool=slot_pool,
        scheduled_occurrences=[],
        working_hours=working_hours,
        max_per_day=2
    )
    assert result == datetime(2025, 7, 7, 9, 0)

def test_next_available_slot_priority(
    planner: CalendarPlanner,
    slot_pool: list[TimeSlot],
    working_hours: list[WorkingHours],
) -> None:
    # Priority shifts slot order
    after = datetime(2025, 7, 6, 8, 0)
    result = planner.next_available_slot(
        after=after,
        slot_pool=slot_pool,
        scheduled_occurrences=[],
        working_hours=working_hours,
        max_per_day=2,
        priority=1
    )
    assert result == datetime(2025, 7, 7, 15, 0)

def test_next_available_slot_none_found(
    planner: CalendarPlanner,
    slot_pool: list[TimeSlot],
    working_hours: list[WorkingHours],
) -> None:
    # All days filled, should return None
    after = datetime(2025, 7, 6, 8, 0)
    occurrences: list[TaskOccurrence] = []
    for d in range(5):
        occurrences.append(make_occurrence(datetime(2025, 7, 7 + d, 9, 0)))
        occurrences.append(make_occurrence(datetime(2025, 7, 7 + d, 15, 0)))
    result = planner.next_available_slot(
        after=after,
        slot_pool=slot_pool,
        scheduled_occurrences=occurrences,
        working_hours=working_hours,
        max_per_day=2
    )
    assert result is None

def test_no_mutation_of_inputs(
    planner: CalendarPlanner,
    slot_pool: list[TimeSlot],
    working_hours: list[WorkingHours],
) -> None:
    after = datetime(2025, 7, 7, 8, 0)
    occurrences = [make_occurrence(datetime(2025, 7, 7, 9, 0))]
    before = list(occurrences)
    _ = planner.is_slot_available(
        proposed_time=datetime(2025, 7, 7, 9, 0),
        scheduled_occurrences=occurrences,
        working_hours=working_hours,
        max_per_day=2,
        slot_pool=slot_pool
    )
    _ = planner.next_available_slot(
        after=after,
        slot_pool=slot_pool,
        scheduled_occurrences=occurrences,
        working_hours=working_hours,
        max_per_day=2
    )
    assert occurrences == before
