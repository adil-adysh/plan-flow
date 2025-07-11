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
- **Validate user-pinned times for manual scheduling intent**

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
        max_per_day: int,
        slot_pool: list[TimeSlot] | None = None
    ) -> bool:
        """Check if a new task can be scheduled at the proposed time.

        Args:
            proposed_time: The datetime to test availability for.
            scheduled_occurrences: List of already scheduled TaskOccurrence.
            working_hours: List of WorkingHours objects for allowed scheduling per weekday.
            max_per_day: Maximum allowed tasks per calendar day.
            slot_pool: Optional list of allowed TimeSlot objects (user preferences). If None, slot-based constraints are skipped.

        Returns:
            True if the slot is available (within working hours, not exceeding per-day cap, not colliding with existing tasks, and matches allowed slots if specified), else False.

        Fallback:
            Returns False if the day is not in working_hours or slot is not allowed.
        """

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

    def is_pinned_time_valid(
        self,
        pinned_time: datetime,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        max_per_day: int
    ) -> bool:
        """Return True if a user-requested pinned datetime is eligible for scheduling."""
````

---

## ⚙️ Constraints

* Day is defined by `proposed_time.date()` or `pinned_time.date()`
* Task count is limited per **calendar day**
* Only times within that day’s `WorkingHours` are eligible
* Time must match a valid `TimeSlot` (for slot-based scheduling)
* **Pinned time may bypass slot pool, but must respect working hours and caps**
* No mutation of inputs
* Search up to 14 days ahead (internal limit for `next_available_slot`)

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
* `slot_pool`: allowed user slot times (may be None for is_slot_available)
* `working_hours`: allowed hours per weekday
* `scheduled_occurrences`: already scheduled task times
* `max_per_day`: how many tasks allowed per day
* `pinned_time`: user-chosen datetime to validate (if applicable)

### Outputs

* `is_slot_available`: `True` or `False`
* `next_available_slot`: first available datetime or `None`
* `is_pinned_time_valid`: `True` or `False` if the exact datetime is acceptable

---

### Type Annotations

* All parameters and return types must be typed
* Use Python 3.11+ syntax: `str | None` instead of `Optional[str]`, `int | str` instead of `Union[int, str]`, etc.
* Use `Literal`, `list[Model]` as needed
* No timezone-aware datetime logic (use naive datetime only)

> **Note:** Do not use legacy `Optional[...]` or `Union[...]` syntax.

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
* **Pinned time valid → accepted**
* **Pinned time invalid → rejected**

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
✅ `is_pinned_time_valid()` added for user-specified times
✅ Fully unit tested with slot edge cases
✅ Typed and linted (Ruff + Pyright strict)
