---
applyTo: "addon/globalPlugins/planflow/task/scheduler_service.py"
---

# Module Instructions — Scheduler Service (v2)

This module implements core logic for **task scheduling, recurrence, retries**, and **slot-aware scheduling decisions**. It must remain pure, testable, and decoupled from NVDA and TinyDB.

---

## ✨ Goals

- Determine whether a task is due, missed, or expired
- Compute the next valid `TaskOccurrence` for a recurring task
- Handle retries while respecting max limits and available user slots
- Respect time slots, working hours, and per-day task caps
- Produce fully deterministic, immutable outputs
- **Honor optional user-pinned times during scheduling if valid**

---

## 📦 Module Contents

Implement the main scheduling engine:

### ✅ `TaskScheduler`

This class handles recurrence, retrying, and determining task states.

---

### Public Methods

```python
class TaskScheduler:

    def is_due(self, occurrence: TaskOccurrence, now: datetime) -> bool:
        """Return True if the task is currently due."""

    def is_missed(self, occurrence: TaskOccurrence, now: datetime) -> bool:
        """Return True if scheduled time has passed and not marked done."""

    def should_retry(self, execution: TaskExecution) -> bool:
        """Check if task is eligible for retry based on RetryPolicy."""

    def get_next_occurrence(
        self,
        task: TaskDefinition,
        from_time: datetime,
        calendar: CalendarPlanner,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        slot_pool: list[TimeSlot],
        max_per_day: int
    ) -> Optional[TaskOccurrence]:
        """Generate the next recurrence occurrence for this task.
        
        If the task includes a valid `pinned_time`, return an occurrence
        for that time. If the pinned time is invalid or missing, use 
        recurrence rules and calendar logic to select the next slot.
        """

    def reschedule_retry(
        self,
        occurrence: TaskOccurrence,
        policy: RetryPolicy,
        now: datetime,
        calendar: CalendarPlanner,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        slot_pool: list[TimeSlot],
        max_per_day: int
    ) -> Optional[TaskOccurrence]:
        """Generate a retry occurrence based on retry policy and availability."""
````

---

## ⚙️ Constraints

* No real-time calls (use `now` parameter only)
* Must honor per-day caps, user time slots, and working hours
* Always return **new objects** — do not mutate inputs
* Return `None` if scheduling isn't possible
* Prioritize preferred time slots for retry/recurrence scheduling
* Tasks with `high` priority should be placed first in day when resolving conflicts
* **Pinned time takes precedence if valid, but must pass calendar validation**

---

## 📚 Requirements

### Inputs

* All models from `task_model.py` (fully typed)
* `CalendarPlanner` handles conflict detection
* `WorkingHours` defines user availability
* `TimeSlot` defines preferred times for task delivery
* `max_per_day`: max task occurrences per calendar day

### Outputs

* Return `TaskOccurrence` or `None` (retry or next recurrence)
* Must be deterministic and side-effect free

---

### Type Annotations

* All inputs/outputs must be fully typed
* Use `Optional`, `Literal`, `datetime`, and model classes
* Use `-> None` explicitly where relevant

---

### Docstrings

Each method must use Google-style docstrings and document:

* What the method does
* Parameter explanations
* Return values
* Constraints (immutability, slot handling, fallback logic)
* **Pinned-time support in `get_next_occurrence()` must be documented**

---

## 🧪 Testing

Write tests in `tests/test_scheduler_service.py`.

### Test Coverage

* `is_due` with edge timestamps
* `is_missed` when overdue but not done
* `should_retry` for zero, partial, and full retries
* `get_next_occurrence` with:

  * recurrence = None
  * recurrence = timedelta
  * no available slot for N days
  * valid `pinned_time` → selected
  * invalid `pinned_time` → fallback
  * varying working hours and slot preferences
* `reschedule_retry` with:

  * retry interval vs next available slot
  * task cap overflow
  * multiple tasks competing for same slot

Use `freezegun` or inject `now` into all tests. Mock or construct `CalendarPlanner` + `WorkingHours`.

---

## 🔒 Exclusions

❌ No NVDA APIs
❌ No DB access
❌ No `datetime.now()` calls
❌ No print/logging or speech
❌ No I/O of any kind

---

## ✅ Completion Criteria

✅ Fully type-annotated and pure
✅ Deterministic and testable in isolation
✅ Respects working hours, slot pool, and task caps
✅ Can return `None` if no valid slot
✅ `get_next_occurrence()` supports valid `pinned_time`
✅ 100% unit tested with all logic branches
✅ Passes Pyright strict + Ruff
