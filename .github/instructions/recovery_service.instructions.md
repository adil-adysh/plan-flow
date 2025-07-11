---
applyTo: "addon/globalPlugins/planflow/task/recovery_service.py"
---

# Module Instructions — Recovery Service (v2)

This module defines the logic to **recover missed task executions** while respecting recurrence, retry policy, working hours, and time slots. It must remain pure and testable.

---

## ✨ Goals

- Detect and recover tasks missed while NVDA was inactive
- Evaluate whether retry or recurrence is possible based on task policy
- Produce rescheduled occurrences that respect user constraints
- Leverage `CalendarPlanner` and `TaskScheduler` for retry placement
- **Skip rescheduling for pinned-time occurrences (user explicit intent)**

---

## 📦 Module Contents

Implement a single public class:

### ✅ `RecoveryService`

This encapsulates analysis of missed tasks and generation of next valid occurrences.

---

### Public Methods

```python
class RecoveryService:

    def recover_missed_occurrences(
        self,
        executions: list[TaskExecution],
        occurrences: dict[str, TaskOccurrence],
        tasks: dict[str, TaskDefinition],
        now: datetime,
        calendar: CalendarPlanner,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        slot_pool: list[TimeSlot],
        max_per_day: int
    ) -> list[TaskOccurrence]:
        """Return new retry or recurrence occurrences for missed tasks.

        When calling TaskScheduler.reschedule_retry, pass the retries_remaining parameter as required by the implementation.

        Occurrences with `pinned_time` are treated as user-fixed and 
        excluded from recovery retry/reschedule logic.
        """
````

---

## ⚙️ Constraints

* Only recover tasks with state `"missed"` or `"pending"` and `scheduled_for < now`
* If recurrence is enabled → generate next scheduled occurrence
* If retry policy allows → generate retry with correct delay
* Use `TaskScheduler` to calculate next occurrence or retry
* Use `CalendarPlanner` to enforce per-day caps and availability
* **Do not recover pinned-time occurrences**
* Inputs must remain unmodified
* Return only valid occurrences that fit user’s available time

---

## 📚 Requirements

### Inputs

* `executions`: all known execution records
* `occurrences`: dict of occurrence\_id → TaskOccurrence
* `tasks`: dict of task\_id → TaskDefinition
* `now`: logical current time
* `calendar`: calendar planner for availability checks
* `working_hours`: active time spans for each weekday
* `slot_pool`: user-preferred time slots
* `max_per_day`: allowed task count per day

### Outputs

* List of new `TaskOccurrence`s (unsaved) ready to be scheduled

---

### Type Annotations

* Fully annotate all parameters and return values
* Use Python 3.11+ syntax: `str | None` instead of `Optional[str]`, `int | str` instead of `Union[int, str]`, etc.
* Use `Literal`, `list[Model]`, and `-> None` as needed

> **Note:** Do not use legacy `Optional[...]` or `Union[...]` syntax.

---

### Docstrings

Use Google-style for all public elements:

* Describe the function
* List all parameters and their meanings
* Return value and assumptions
* Mention immutability of inputs
* Document that `pinned_time` disables recovery logic for that occurrence

---

## 🧪 Testing

Write all test cases in `tests/test_recovery_service.py`.

### Test Scenarios

* Missed task with retries available → successful retry scheduled
* Retry fails due to no slots → not returned
* Task with recurrence → next valid slot selected
* Task with retry + recurrence → only one scheduled
* Retry limit exceeded → no action
* Working hour/slot limits prevent scheduling → fallback or skip
* **Pinned occurrence → ignored during recovery**

Use `FakeClock` or inject `now` into test cases. Construct tasks, slots, hours manually.

---

## 🔒 Exclusions

❌ No NVDA API usage
❌ No I/O, database, or speech output
❌ No real-time system access
❌ No mutation of passed-in arguments

---

## ✅ Completion Criteria

✅ Implements `recover_missed_occurrences()` fully
✅ Leverages `TaskScheduler` and `CalendarPlanner`
✅ Respects user-configured limits and slot/working-hour windows
✅ Ignores pinned-time occurrences during recovery
✅ 100% test coverage with edge cases
✅ Pure, typed, and deterministic
✅ Passes Ruff + Pyright strict
