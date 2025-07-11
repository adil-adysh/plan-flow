---
module: "addon/globalPlugins/planflow/task/calendar_planner.py"
type: "unit-test-plan"
title: "CalendarPlanner Unit Test Plan"
---

# 🧪 CalendarPlanner Unit Test Plan

This test plan covers **unit test scenarios** for the `CalendarPlanner`, including slot validation, working hours, and scheduling logic.

---

## ✅ Test Case Matrix

| Test Name | Description |
|-----------|-------------|
| `test_slot_available_within_working_hours` | Slot available within working hours → should return True. |
| `test_slot_not_in_allowed_slots` | Slot not in allowed slots → should return False. |
| `test_day_filled_max_per_day` | Day filled (max_per_day reached) → should return False. |
| `test_skips_holidays_no_working_hours` | Skips holidays (no working hours entry). |
| `test_next_available_slot` | Finds next available slot after a given time. |
| `test_next_available_slot_respects_caps` | Respects per-day task caps. |
| `test_pinned_time_valid` | Pinned time valid → accepted. |
| `test_pinned_time_invalid` | Pinned time invalid → rejected. |

---

## 📦 Unit Scope

| Component             | Role                                      |
|----------------------|--------------------------------------------|
| `CalendarPlanner`    | Validates slot, working hours, and caps    |

---

## 🧪 Test Enablers

### Fixtures
- Deterministic slot pools and working hour configs

### Tools
- `pytest`

---

## ✅ Completion Criteria

- [ ] All test cases implemented in `tests/test_calendar_planner.py`
- [ ] All assertions verified with no Pyright or Ruff errors
- [ ] Works with `--tb=short -v -s` and CI environments

---

## 📂 Suggested File Location

- `tests/test_calendar_planner.py`
