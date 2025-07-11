---
applyTo: "addon/globalPlugins/planflow/task/smart_scheduler_controller.py"
---

# 🧭 Module Instructions — SmartSchedulerController

This module defines a high-level **coordination and delegation layer** over `SmartSchedulerService`. It provides a simplified, testable interface for controlling task scheduling, retry, recovery, and timer state without duplicating underlying logic.

It is designed to be used by UI/event layers and tests that need **high-level commands** such as `mark_done`, `retry_task`, `recover_all`, or `get_scheduled_occurrences`.

---

## ✨ Goals

- Expose **declarative control** over SmartSchedulerService
- Bridge between UI and the lower-layer scheduling components
- Forward relevant calls to the appropriate services
- Handle task/occurrence validation, fallback, and error safety
- Remain modular, testable, and NVDA/UI-independent

---

## 📦 Public Class: `SmartSchedulerController`

### Required Dependencies

```python
class SmartSchedulerController:
    def __init__(
        self,
        smart_scheduler: SmartSchedulerService,
        repo: ExecutionRepository,
        scheduler: TaskScheduler,
        recovery: RecoveryService,
        calendar: CalendarPlanner,
        now_fn: Callable[[], datetime] = datetime.now
    ): ...
````

---

### ✅ Public Methods

| Method                          | Purpose                                                                     |
| ------------------------------- | --------------------------------------------------------------------------- |
| `start()`                       | Start the scheduler, schedule all valid future tasks, check for missed ones |
| `pause()`                       | Pause all scheduling and timers                                             |
| `resume()`                      | Resume paused state and schedule all valid tasks                            |
| `mark_done(occ_id: str)`        | Mark a `TaskOccurrence` as done, and schedule retry or recurrence           |
| `retry_occurrence(occ_id: str)` | Manually trigger retry if allowed by policy                                 |
| `get_scheduled_occurrences()`   | Return currently scheduled `TaskOccurrence`s                                |
| `recover_missed_tasks()`        | Run recovery for all missed and eligible tasks                              |

---

## ⚙️ Constraints

* Do not replicate any timer logic or scheduling rules — always delegate to `SmartSchedulerService`, `TaskScheduler`, or `RecoveryService`
* Validate that `occurrence_id` or `task_id` exists before calling downstream methods
* Must use only injected dependencies — no global imports or `datetime.now()` directly
* Raise `ValueError` with clear message if `occurrence` or `task` is missing
* No NVDA, speech, print, or file I/O

---

## 📝 Docstrings

Use Google-style docstrings.

Each method should clearly document:

* Purpose
* Parameters
* Return values
* Errors raised (e.g., missing task or occurrence)
* Side effects (e.g., schedules new retry/recur occurrence)

---

## 🔍 Internal Helpers (Optional)

These may be implemented as private methods:

* `_get_occurrence(occ_id: str) -> TaskOccurrence`
* `_get_task(task_id: str) -> TaskDefinition`
* `_already_done(occ_id: str) -> bool`

---

## 🧪 Testing Guidelines

Write test cases in `tests/integration/test_smart_scheduler_controller.py`

### Required Tests

| Test Case                                                 | Description                                                                              |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `test_start_schedules_and_recovers`                       | Verifies `start()` calls `schedule_all()` and recovery on SmartSchedulerService          |
| `test_mark_done_creates_execution_and_schedules_retry`    | Marks a task as done, and verifies that retry is created and scheduled                   |
| `test_mark_done_falls_back_to_recurrence`                 | If retry is exhausted, recurrence is scheduled                                           |
| `test_retry_occurrence_returns_occurrence_if_valid`       | Tests retry logic returns new occurrence if allowed                                      |
| `test_retry_occurrence_returns_none_if_retry_exhausted`   | Retry returns None if retry policy is exhausted                                          |
| `test_resume_triggers_schedule_all`                       | Calling `resume()` after pause triggers scheduling again                                 |
| `test_get_scheduled_occurrences_returns_expected_set`     | Ensures the correct future scheduled tasks are returned                                  |
| `test_recover_missed_tasks_delegates_to_recovery_service` | Verifies missed task recovery triggers and returns new tasks                             |
| `test_invalid_occurrence_id_raises`                       | `mark_done` and `retry_occurrence` should raise `ValueError` if occurrence doesn't exist |

---

## ✅ Completion Criteria

* Fully type-annotated public interface using Python 3.11+ syntax (`str | None`, not `Optional[...]`)
* Pure coordination logic only — no business rules, no threading
* Docstrings provided for all public methods
* Passes `ruff` and `pyright --strict`
* 100% test coverage via `pytest`
* Exposes stable command interface for UI and CLI layers

---

## 📁 Suggested File Structure

```plaintext
addon/globalPlugins/planflow/task/smart_scheduler_controller.py
tests/integration/test_smart_scheduler_controller.py
```

---

> 🔄 This controller simplifies integration, ensures testability, and gives UIs a stable API over the smart scheduler's behavior without duplicating logic or state.
