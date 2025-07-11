---
module: "addon/globalPlugins/planflow/task/smart_scheduler_service.py"
type: "integration-test-plan"
title: "SmartSchedulerService Integration Test Plan"
---

# 🧪 SmartSchedulerService Integration Test Plan

This test plan covers **integration scenarios** where `SmartSchedulerService` interacts with:

- `ExecutionRepository`
- `TaskScheduler`
- `CalendarPlanner`
- `RecoveryService`

These tests validate end-to-end coordination of scheduling, timing, retry, recurrence, and recovery workflows.

---

## ✅ Test Case Matrix

| Test Name | Description |
|-----------|-------------|
| `test_schedule_all_only_schedules_future_and_pending_occurrences` | Verifies that `schedule_all()` only schedules future `TaskOccurrence`s that are not already marked as "done". |
| `test_timer_trigger_records_execution_and_schedules_retry` | Simulates a timer firing and checks that the task is marked done and a retry `TaskOccurrence` is generated and scheduled. |
| `test_timer_trigger_records_execution_and_schedules_recurrence` | Validates that when retry is not applicable but recurrence is present, a new occurrence is scheduled based on recurrence rules. |
| `test_schedule_occurrence_skips_if_slot_unavailable` | Ensures `schedule_occurrence()` does not create timers for occurrences in invalid time slots. |
| `test_pause_prevents_timer_execution_and_scheduling` | Verifies that paused state prevents all scheduling, including future and missed tasks. |
| `test_resume_after_pause_restarts_scheduling_of_valid_occurrences` | Ensures that calling `start()` after pause reschedules all future valid `TaskOccurrence`s. |
| `test_check_for_missed_tasks_triggers_immediate_execution_within_grace` | Simulates a task missed by less than `_RECOVERY_GRACE_SECONDS` and confirms it's triggered immediately. |
| `test_check_for_missed_tasks_delegates_to_recovery_service_beyond_grace` | Ensures tasks missed beyond grace are passed to `RecoveryService.recover_missed_occurrences`. |
| `test_recovery_service_returns_multiple_rescheduled_occurrences` | Simulates `RecoveryService` returning multiple retry/recurred occurrences and verifies they’re all scheduled. |
| `test_schedule_occurrence_replaces_existing_timer_for_same_occurrence` | Ensures previously scheduled timers for the same `TaskOccurrence` are replaced to avoid duplicate triggers. |
| `test_on_trigger_respects_retry_limits_and_falls_back_to_recurrence` | Confirms that if retry is not allowed or exhausted, recurrence is attempted as fallback. |
| `test_on_trigger_skips_if_task_definition_missing` | Ensures that if a task definition is no longer available in `ExecutionRepository`, no scheduling is attempted. |
| `test_schedule_occurrence_skips_if_occurrence_already_executed` | Validates that `schedule_occurrence()` checks for completion before scheduling. |
| `test_check_for_missed_tasks_skips_executed_occurrences` | Ensures that missed check skips already "done" occurrences even if their time has passed. |
| `test_trigger_recovery_gracefully_handles_empty_recovery_output` | Validates that recovery returns empty list without raising or attempting to schedule. |

---

## 📦 Integration Scope

| Component             | Role                                                                 |
|-----------------------|----------------------------------------------------------------------|
| `ExecutionRepository` | Provides occurrence, task, and execution persistence APIs            |
| `TaskScheduler`       | Determines retry and recurrence logic for triggered tasks            |
| `CalendarPlanner`     | Determines if a time slot is valid given task caps and working hours |
| `RecoveryService`     | Suggests retry/reschedule tasks based on missed execution analysis   |
| `SmartSchedulerService` | Orchestrates all above modules to coordinate real-time task handling |

---

## 🧪 Test Enablers

### Fixtures
- `now_fn`: controllable `datetime.now()` injector
- `threading.Event` or `threading.Timer` stubs to simulate trigger delays
- Mocks for repository/scheduler/calendar/recovery

### Tools
- `pytest`
- `freezegun` (optional for timer edge control)
- `unittest.mock` for behavior assertions

---

## ✅ Completion Criteria

- [ ] All test cases implemented in `tests/integration/test_smart_scheduler_service.py`
- [ ] At least one test verifies retry→recur fallback behavior
- [ ] All assertions verified with no Pyright or Ruff errors
- [ ] Works with `--tb=short -v -s` and CI environments
- [ ] Simulates real-world planner behaviors using realistic slots and hours

---

## 📂 Suggested File Location

- `tests/integration/test_smart_scheduler_service.py`
