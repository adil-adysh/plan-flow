---
module: "addon/globalPlugins/planflow/task/recovery_service.py"
type: "unit-test-plan"
title: "RecoveryService Unit Test Plan"
---

# 🧪 RecoveryService Unit Test Plan

This test plan covers **unit test scenarios** for the `RecoveryService`, including detection and recovery of missed tasks.

---

## ✅ Test Case Matrix

| Test Name | Description |
|-----------|-------------|
| `test_recover_missed_occurrences_with_retries` | Missed task with retries available → schedules retry. |
| `test_recover_missed_occurrences_no_slots` | Retry fails due to no slots → not returned. |
| `test_recover_missed_occurrences_with_recurrence` | Task with recurrence → next valid slot selected. |
| `test_recover_missed_occurrences_retry_and_recur` | Task with retry + recurrence → only one scheduled. |
| `test_recover_missed_occurrences_retry_limit_exceeded` | Retry limit exceeded → no action. |
| `test_recover_missed_occurrences_caps_prevent_scheduling` | Working hour/slot limits prevent scheduling → fallback or skip. |
| `test_recover_missed_occurrences_pinned_ignored` | Pinned occurrence → ignored during recovery. |

---

## 📦 Unit Scope

| Component             | Role                                      |
|----------------------|--------------------------------------------|
| `RecoveryService`    | Handles missed task analysis and recovery  |

---

## 🧪 Test Enablers

### Fixtures
- FakeClock or injected now
- Manual construction of tasks, slots, and hours

### Tools
- `pytest`

---

## ✅ Completion Criteria

- [ ] All test cases implemented in `tests/test_recovery_service.py`
- [ ] All assertions verified with no Pyright or Ruff errors
- [ ] Works with `--tb=short -v -s` and CI environments

---

## 📂 Suggested File Location

- `tests/test_recovery_service.py`
