"""Unit tests for CalendarPlanner logic (per-day task limits, slot availability, next valid day).

Covers: is_slot_available, next_available_day
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional

from addon.globalPlugins.planflow.task.calendar_planner import CalendarPlanner

# Minimal TaskOccurrence stub for testing
class TaskOccurrence:
    def __init__(self, scheduled_for: datetime):
        self.scheduled_for = scheduled_for

@pytest.fixture
def base_time() -> datetime:
    return datetime(2025, 7, 10, 9, 0, 0)

@pytest.fixture
def planner() -> CalendarPlanner:
    return CalendarPlanner()

@pytest.mark.parametrize("occurrence_times,max_per_day,proposed_time,expected", [
    # Fewer than max tasks on day: available
    ([datetime(2025, 7, 10, 8)], 2, datetime(2025, 7, 10, 10), True),
    # Equal to max: unavailable
    ([datetime(2025, 7, 10, 8), datetime(2025, 7, 10, 12)], 2, datetime(2025, 7, 10, 14), False),
    # Tasks on other days ignored
    ([datetime(2025, 7, 9, 8), datetime(2025, 7, 11, 8)], 1, datetime(2025, 7, 10, 10), True),
    # No tasks scheduled: available
    ([], 1, datetime(2025, 7, 10, 10), True),
])
def test_is_slot_available(occurrence_times, max_per_day, proposed_time, expected, planner):
    occurrences = [TaskOccurrence(t) for t in occurrence_times]
    result = planner.is_slot_available(proposed_time, occurrences, max_per_day)
    assert result is expected

@pytest.mark.parametrize("occurrence_times,max_per_day,after,expected", [
    # Next day is available
    ([datetime(2025, 7, 10, 8), datetime(2025, 7, 10, 12)], 2, datetime(2025, 7, 10, 13), datetime(2025, 7, 11, 0, 0, 0)),
    # Skips filled days
    ([datetime(2025, 7, 10, 8), datetime(2025, 7, 10, 12), datetime(2025, 7, 11, 9), datetime(2025, 7, 11, 10)], 2, datetime(2025, 7, 10, 13), datetime(2025, 7, 12, 0, 0, 0)),
    # Returns None if no slot in window (simulate 3-day window)
    ([datetime(2025, 7, 10, 8), datetime(2025, 7, 10, 12), datetime(2025, 7, 11, 9), datetime(2025, 7, 11, 10), datetime(2025, 7, 12, 9), datetime(2025, 7, 12, 10)], 2, datetime(2025, 7, 10, 13), None),
    # Available same day if after is before midnight and slot exists
    ([datetime(2025, 7, 10, 8)], 2, datetime(2025, 7, 10, 7), datetime(2025, 7, 10, 0, 0, 0)),
])
def test_next_available_day(occurrence_times, max_per_day, after, expected, planner):
    occurrences = [TaskOccurrence(t) for t in occurrence_times]
    result = planner.next_available_day(after, occurrences, max_per_day)
    assert result == expected

# Edge: scheduled_occurrences is not mutated
def test_no_mutation_of_inputs(planner, base_time):
    occurrences = [TaskOccurrence(base_time)]
    before = list(occurrences)
    _ = planner.is_slot_available(base_time, occurrences, 1)
    _ = planner.next_available_day(base_time, occurrences, 1)
    assert occurrences == before
