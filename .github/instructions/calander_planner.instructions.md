---
applyTo: "addon/globalPlugins/planflow/task/calendar_planner.py"
---

# Module Instructions — Calendar Planner (v2)

This module provides logic to validate and compute **valid scheduling windows** for tasks. It enforces working hours, daily limits, and slot preferences.

---

## ✨ Goals

- Enforce working hours and time slot constraints per weekday
- Check if a task occurrence can be scheduled at a given time
- Compute the next available slot for retries or recurrence
- Respect per-day task caps and avoid time collisions

---

## 📦 Module Contents

Implement the following public class:

### ✅ `CalendarPlanner`

This encapsulates availability logic based on configured user constraints.

---

### Public Methods

```python
class CalendarPlanner:

    def is_slot_available(
        self,
        proposed_time: datetime,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        max_per_day: int
    ) -> bool:
        """Check if a new task can be scheduled at the proposed time."""

    def next_available_slot(
        self,
        after: datetime,
        slot_pool: list[TimeSlot],
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        max_per_day: int,
        priority: Optional[int] = None
    ) -> Optional[datetime]:
        """Find the next available valid datetime for scheduling."""
````

---

## ⚙️ Constraints

* Day is defined by `proposed_time.date()`
* Task count is limited per **calendar day**
* Only times within that day’s `WorkingHours` are eligible
* Time must match a valid `TimeSlot` (within hours)
* No mutation of inputs
* Search up to 14 days ahead (internal limit)

---

## 📚 Definitions

### `WorkingHours`

A weekday-to-hours map, e.g.:

```python
{
  "monday": TimeRange(start=19:00, end=22:00),
  "saturday": TimeRange(start=8:30, end=22:00),
}
```

### `TimeSlot`

User-defined preferred times, such as:

```python
[
  TimeSlot(name="morning", hour=8, minute=30),
  TimeSlot(name="evening", hour=20, minute=0),
]
```

---

## 📚 Requirements

### Inputs

* `after`: datetime to search after
* `slot_pool`: allowed user slot times
* `working_hours`: allowed hours per weekday
* `scheduled_occurrences`: already scheduled task times
* `max_per_day`: how many tasks allowed per day

### Outputs

* `is_slot_available`: `True` or `False`
* `next_available_slot`: first available datetime or `None`

---

### Type Annotations

* All parameters and return types must be typed
* Use `Optional[...]`, `Literal[...]`, `list[Model]`
* No timezone-aware datetime logic (use naive datetime only)

---

### Docstrings

Each method must include:

* Purpose
* Parameter docs
* Return description
* Explain fallback behavior

Use Google-style.

---

## 🧪 Testing

Write all test cases in `tests/test_calendar_planner.py`.

### Scenarios

* Available slot within working hours → success
* Time not in allowed slots → skipped
* Day filled → try next day
* Skips holidays (no working hours entry)
* Preference fallback — if `priority` affects slot ordering

Use deterministic slot pools and working hour configs in tests.

---

## 🔒 Exclusions

❌ No NVDA or real-time clock access
❌ No external storage or I/O
❌ No mutation of input collections
❌ No logging or side effects

---

## ✅ Completion Criteria

✅ Implements all required methods
✅ Fully pure and side-effect free
✅ Respects working hours, time slots, and limits
✅ Fully unit tested with slot edge cases
✅ Typed and linted (Ruff + Pyright strict)
