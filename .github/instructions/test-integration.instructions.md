---
applyTo: "tests/integration/**/*.py"
---

# Integration Testing Instructions — PlanFlow Add-on

This file defines the structure and expectations for **integration tests** across the PlanFlow task scheduler. Integration tests verify realistic behavior across multiple modules (e.g. `TaskScheduler`, `CalendarPlanner`, and model definitions), while preserving PlanFlow’s purity and testability standards.

---

## ✨ Goals

- Simulate full scheduling and recovery flows across services
- Validate fallback behaviors like retry or pinned-time overrides
- Use `TaskDefinition`, `TaskOccurrence`, `CalendarPlanner`, and `TaskScheduler` together
- Ensure logic remains deterministic, typed, and NVDA-free
- Test interactions such as slot constraints, recurrence rules, per-day caps, and pinned-time blocking

---

## 📦 Test Types to Include

Integration tests should cover full logic chains across modules:

| Scenario                          | Expected Coverage                         |
|-----------------------------------|--------------------------------------------|
| Pinned time success               | CalendarPlanner + Scheduler                |
| Pinned time invalid → fallback    | Scheduler → slot-based resolution          |
| Max per-day cap prevents schedule | CalendarPlanner enforces cap               |
| Retry allowed within limits       | Execution + RetryPolicy + Scheduler        |
| Recovery flow skips pinned        | RecoveryService honors user intent         |
| Recurrence + slot constraint      | Scheduler + CalendarPlanner slot filtering |

---

## 🧱 File Naming & Location

- Location: `tests/integration/`
- File names must start with `test_`
- Use one file per flow type:

```text
tests/integration/
├── test_scheduler_flow.py
├── test_recovery_flow.py
├── test_calendar_integration.py
````

---

## 📚 Requirements

### Inputs

* `now: datetime` — injected, fixed logical time
* `working_hours`: list of active hours per weekday
* `slot_pool`: preferred delivery times (list of `TimeSlot`)
* `TaskDefinition`: task intent (with or without pinned\_time)
* `TaskOccurrence`: existing scheduled tasks
* `TaskExecution`: runtime task state (optional)

### Outputs

* Expected `TaskOccurrence` if successful
* `None` if scheduling is blocked
* Verification of fallback or skip behavior

---

## 🧪 Testing Guidelines

* Use real models and services — no mocks
* Always inject `now` instead of using `datetime.now()`
* Use `pytest.fixture` for test inputs
* Use `@pytest.mark.parametrize` for edge case variation
* Prefer minimal but realistic simulations (e.g., already booked slots)

---

### Example Integration Test Case

```python
def test_fallback_when_pinned_time_conflicts():
    now = datetime(2025, 1, 13, 8, 0)
    calendar = CalendarPlanner()
    scheduler = TaskScheduler()

    task = TaskDefinition(
        id="task-3",
        title="Pinned Meeting",
        created_at=now,
        recurrence=None,
        preferred_slots=["morning"],
        priority="medium",
        retry_policy=RetryPolicy(max_retries=0),
        pinned_time=datetime(2025, 1, 13, 9, 0),
    )

    occurrence = scheduler.get_next_occurrence(
        task=task,
        from_time=now,
        calendar=calendar,
        scheduled_occurrences=[...],  # already booked slot at 9:00
        working_hours=[...],
        slot_pool=[...],
        max_per_day=2
    )

    assert occurrence is None  # fallback fails because no slot available
```

---

## ⚙️ Type Annotations

* All tests must use full type annotations for fixtures and inputs
* Use Python 3.11+ syntax: `str | None` instead of `Optional[str]`, `int | str` instead of `Union[int, str]`, etc.
* Use `list[...]`, `datetime`, and model types as needed
* Fixtures must return concrete types (`-> list[WorkingHours]`, etc.)

> **Note:** Do not use legacy `Optional[...]` or `Union[...]` syntax.

---

## 🧪 Testing Tools

| Tool                     | Purpose                         |
| ------------------------ | ------------------------------- |
| Pytest                   | Test runner                     |
| Pyright                  | Type verification (strict)      |
| Ruff                     | Linting                         |
| Freezegun / injected now | Time mocking (manual preferred) |

---

## 🔒 Exclusions

❌ No NVDA or speech APIs
❌ No I/O or filesystem access
❌ No real-time system clock
❌ No mutation of global state
❌ No mocking of services like `CalendarPlanner` or `TaskScheduler`

---

## ✅ Completion Criteria

✅ One integration test per key scheduling flow
✅ Fully deterministic and isolated
✅ All test files use fixtures and injected datetime
✅ At least one test covers pinned-time fallback logic
✅ Compatible with `pytest`, `pyright`, and `ruff`
✅ Passes with `pytest tests/integration/`
