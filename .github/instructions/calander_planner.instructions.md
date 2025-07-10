---
applyTo: "addon/globalPlugins/planflow/task/calendar_planner.py"
---

# Module Instructions — Calendar Planner

This module provides logic to **validate and compute available scheduling slots** for tasks. It helps enforce constraints like **maximum tasks per day**, **conflict avoidance**, and **rescheduling availability**.

---

## ✨ Goals

- Enforce per-day task limits
- Check if a task occurrence can be scheduled at a given time
- Compute next valid day/time for retries or recurrence
- Integrate with recovery and scheduler modules without duplication

---

## 📦 Module Contents

Implement a single public class:

### ✅ `CalendarPlanner`

Encapsulates task scheduling constraints and availability.

---

### Public Methods

```python
class CalendarPlanner:

    def is_slot_available(
        self,
        proposed_time: datetime,
        scheduled_occurrences: list[TaskOccurrence],
        max_per_day: int
    ) -> bool:
        """Check if a new task can be scheduled at the given time."""

    def next_available_day(
        self,
        after: datetime,
        scheduled_occurrences: list[TaskOccurrence],
        max_per_day: int
    ) -> Optional[datetime]:
        """Return the next datetime where a slot is available for scheduling."""
````

---

## ⚙️ Constraints

* Count tasks per day (not per hour)
* Use only `scheduled_occurrences`, not persistent DB
* Day is defined as local calendar date (`dt.date()`), not 24h rolling
* Return `None` if no slot is found in the next N days (set limit internally)
* No mutation of input arguments

---

## 📚 Requirements

### Inputs

* `proposed_time`: Time to test availability for
* `scheduled_occurrences`: All current task occurrences (future or pending)
* `max_per_day`: Maximum allowed tasks per day

### Outputs

* Boolean result for `is_slot_available`
* Optional `datetime` for `next_available_day`

---

### Type Annotations

* Full annotations for all inputs and return values
* Use `Optional`, `Literal`, and model imports as needed
* Support only timezone-naive datetimes (no `pytz` or `zoneinfo`)

---

### Docstrings

Use Google-style docstrings for:

* Each method (describe parameters, return values, and behavior)
* Class summary (why this exists and what it handles)

---

## 🧪 Testing

Write full unit tests in `test_calendar_planner.py`.

### Test Coverage

* `is_slot_available()`:

  * Fewer than max tasks = available
  * Equal to max = unavailable
  * Tasks on other days ignored

* `next_available_day()`:

  * Finds next day with available space
  * Skips filled days
  * Returns None if no availability in search window

Use fixed `datetime` objects and pass `scheduled_occurrences` explicitly (no real-time reads).

---

## 🔒 Exclusions

❌ No NVDA APIs
❌ No real-time functions
❌ No file or DB access
❌ No mutation of inputs
❌ No logging or speech

---

## ✅ Completion Criteria

✅ Implements both methods fully
✅ Enforces per-day limits correctly
✅ Fully typed, pure, and side-effect free
✅ 100% unit tested with edge cases
✅ Lint- and type-check clean
✅ Compatible with recovery/scheduler modules
