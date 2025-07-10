---
applyTo: "addon/globalPlugins/planflow/task/recovery_service.py"
---

# Module Instructions — Recovery Service

This module defines the logic to detect and recover **missed or overdue task executions**. It works in coordination with the `TaskScheduler` and models from `task_model.py`.

---

## ✨ Goals

- Recover tasks missed while NVDA was inactive or scheduling was paused
- Determine which missed tasks should be retried or skipped
- Generate appropriate retry or recurrence occurrences
- Respect user-defined retry policies and per-day limits (delegated to planner)

---

## 📦 Module Contents

Implement a single public class:

### ✅ `RecoveryService`

Encapsulates logic for analyzing missed tasks and suggesting next steps.

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
    ) -> list[TaskOccurrence]:
        """Recover retry or recurrence for missed tasks.

        Returns a list of new TaskOccurrences that should be scheduled next.
        """
````

---

## ⚙️ Constraints

* Only recover tasks with state "missed" or "pending" and `scheduled_for < now`
* If recurrence is enabled, generate the next occurrence
* If retries remain, reschedule based on retry interval
* Use helper methods from `TaskScheduler`
* Do **not** modify inputs — return new `TaskOccurrence`s only

---

## 📚 Requirements

### Inputs

* `executions`: All known executions (including missed)
* `occurrences`: Dict of occurrence\_id → TaskOccurrence
* `tasks`: Dict of task\_id → TaskDefinition
* `now`: Logical clock (no real-time reading)

### Outputs

* A list of new `TaskOccurrence`s to schedule

---

### Type Annotations

* Full annotations for all parameters and return types
* Use `Literal[...]`, `Optional[...]`, and custom model classes

---

### Docstrings

Use Google-style docstrings for:

* Class and method descriptions
* Parameter explanation
* Return value meaning
* Note that returned occurrences are unsaved

---

## 🧪 Testing

All logic must be unit testable with `pytest`.

**Scenarios to cover:**

* Missed task with retries available → reschedule retry
* Missed task with recurrence only → schedule next recurring occurrence
* Retry limit exceeded → no reschedule
* Multiple missed tasks handled correctly
* Ensure no mutation of input data

Use `FakeClock` or pass `now: datetime` into test cases.

---

## 🔒 Exclusions

❌ No NVDA API usage
❌ No actual database or storage access
❌ No state mutation (only return new objects)
❌ No print/logging or file I/O

---

## ✅ Completion Criteria

✅ Implements `recover_missed_occurrences()`
✅ Fully pure, typed, and deterministic
✅ Proper use of `TaskScheduler` methods
✅ Tested with all major branches and edge cases
✅ Compatible with TinyDB serialization
✅ Pyright strict + Ruff clean
