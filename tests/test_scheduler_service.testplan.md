---
module: "addon/globalPlugins/planflow/task/scheduler_service.py"
type: "unit-test-plan"
title: "TaskScheduler Unit Test Plan"
---

# 🧪 TaskScheduler Unit Test Plan

This test plan covers **unit test scenarios** for the `TaskScheduler`, including recurrence, retry, and scheduling logic.

---

## ✅ Test Case Matrix

| Test Name | Description |
|-----------|-------------|
| `test_is_due` | Returns True for due tasks. |
| `test_is_missed` | Returns True for overdue tasks not marked done. |
| `test_should_retry` | Returns True/False based on retry policy. |
| `test_get_next_occurrence` | Returns correct next slot for recurrence. |
| `test_get_next_occurrence_with_pinned_time` | Handles valid and invalid pinned times. |
| `test_get_next_occurrence_no_available_slot` | No available slot for N days → returns None. |
| `test_reschedule_retry` | Returns correct retry occurrence. |
| `test_reschedule_retry_task_cap_overflow` | Task cap overflow prevents retry. |

---

## 📦 Unit Scope

| Component             | Role                                      |
|----------------------|--------------------------------------------|
| `TaskScheduler`      | Handles recurrence, retry, and slot logic  |

---

## 🧪 Test Enablers

### Fixtures
- Mocked CalendarPlanner, WorkingHours, and slot pools

### Tools
- `pytest`

---

## ✅ Completion Criteria

- [ ] All test cases implemented in `tests/test_scheduler_service.py`
- [ ] All assertions verified with no Pyright or Ruff errors
- [ ] Works with `--tb=short -v -s` and CI environments

---

## 📂 Suggested File Location

- `tests/test_scheduler_service.py`
