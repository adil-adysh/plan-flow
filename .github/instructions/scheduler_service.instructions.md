
---
applyTo: "addon/globalPlugins/planflow/task/scheduler_service.py"
---

# Module Instructions — Scheduler Service

This module implements the **core logic** for task scheduling, recurrence, and retry management. It uses data models from `task_model.py` and must remain **pure**, **testable**, and **NVDA-independent**.

---

## ✨ Goals

- Determine whether tasks are due, missed, or expired
- Generate new `TaskOccurrence` from `TaskDefinition` (recurrence)
- Decide whether to reschedule missed tasks
- Enforce retry limits using `RetryPolicy`
- Derive the next available day via constraints (delegated to calendar)

---

## 📦 Module Contents

Implement a single public class:

### ✅ `TaskScheduler`

Encapsulates scheduling logic and policies.

---

### Public Methods

```python
class TaskScheduler:

    def is_due(self, occurrence: TaskOccurrence, now: datetime) -> bool:
        """Check if a task occurrence is currently due."""

    def is_missed(self, occurrence: TaskOccurrence, now: datetime) -> bool:
        """Determine if an occurrence has passed and was not marked complete."""

    def get_next_occurrence(self, task: TaskDefinition, from_time: datetime) -> Optional[TaskOccurrence]:
        """Return the next scheduled occurrence based on recurrence, or None."""

    def should_retry(self, execution: TaskExecution) -> bool:
        """Return True if the task should be retried, based on retry policy."""

    def reschedule_retry(self, occurrence: TaskOccurrence, policy: RetryPolicy, now: datetime) -> TaskOccurrence:
        """Return a new occurrence based on retry_interval from now."""
````

---

## ⚙️ Constraints

* Must not mutate inputs — always return new objects
* No time reads — accept `now: datetime` as input
* All recurrence logic must honor `task.recurrence`
* Retry logic must respect `max_retries`, `retry_interval`

---

## 📚 Requirements

### Type Annotations

* All parameters and return types must be annotated
* Use `Optional[...]`, `Literal[...]` and `-> None` explicitly
* Use `TaskDefinition`, `TaskOccurrence`, `TaskExecution`, `RetryPolicy` from `task_model.py`

### Docstrings

Each method must use Google-style docstrings:

* Describe behavior
* List parameters
* List return values
* Mention immutability where relevant

---

## 🧪 Testing

This module must be 100% unit testable. All behavior must be covered in `test_scheduler_service.py`.

### Required Test Coverage:

* `is_due` with before/after edge cases
* `is_missed` logic based on time
* `get_next_occurrence` with recurrence = None / timedelta
* `should_retry` based on retry count
* `reschedule_retry` returns new task with correct time offset

Use `FakeClock` or `freezegun` in tests (but do not depend on real `datetime.now()` inside this module).

---

## 🔒 Exclusions

❌ No NVDA API access
❌ No persistence/database access
❌ No speech or I/O side effects
❌ No direct time reads (`datetime.now()`)

---

## ✅ Completion Criteria

✅ All public methods defined and documented
✅ Fully type-annotated, pure functions
✅ No side effects or mutable input modification
✅ Independent of NVDA and external modules
✅ Passes Pyright + Ruff
✅ Supports 100% offline test coverage

---
