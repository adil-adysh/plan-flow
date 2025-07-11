---
applyTo: "addon/globalPlugins/planflow/task/scheduling_tick.py"
---

# Module Instructions — Scheduling Tick Driver

This module provides a **pure, tick-based scheduling driver** for PlanFlow. It replaces the need for background schedulers like APScheduler by using a single function `tick(now)` that orchestrates task scheduling, retries, and recovery at a specific moment in time.

---

## ✨ Goals

- Encapsulate all one-tick scheduling decisions
- Invoke retry, recurrence, and recovery logic in one place
- Return new task occurrences to be scheduled or alerted
- Be **pure, deterministic**, and **unit-testable**
- Avoid real-time APIs or background threading

---

## 📦 Module Contents

Implement a single public function:

### ✅ `tick(now: datetime, repo: ExecutionRepository, calendar: CalendarPlanner, scheduler: TaskScheduler, max_per_day: int, working_hours: list[WorkingHours], slot_pool: list[TimeSlot]) -> list[TaskOccurrence]`

Executes one scheduling tick. Gathers missed or due tasks and generates new `TaskOccurrence`s as needed.

---

## ⚙️ Responsibilities

- Load tasks, occurrences, and executions from `ExecutionRepository`
- Use `TaskScheduler` to detect due/missed tasks
- Use `RecoveryService` to suggest retries or recurrences
- Use `CalendarPlanner` to validate slot availability
- Return new task occurrences (not persisted yet)

---

## 📚 Parameters

| Name            | Type                    | Description |
|-----------------|-------------------------|-------------|
| `now`           | `datetime`              | Logical clock for this tick |
| `repo`          | `ExecutionRepository`   | Task data source |
| `calendar`      | `CalendarPlanner`       | Validates available slots |
| `scheduler`     | `TaskScheduler`         | Determines recurrence, retry, due/missed |
| `max_per_day`   | `int`                   | Daily scheduling cap |
| `working_hours` | `list[WorkingHours]`    | Per-day allowed hours |
| `slot_pool`     | `list[TimeSlot]`        | All named time slots |

---

## 🧪 Testing

Create unit tests in `tests/test_scheduling_tick.py`.

### Test coverage should include:

- Task is due → included in result
- Task missed → retried if allowed
- Recurrence → next instance returned
- No slots available → task skipped
- Retry limit exceeded → nothing returned
- All helper modules are correctly integrated

Use mocked repositories or in-memory data.

---

## ✅ Completion Criteria

✅ Implements `tick()` function  
✅ Fully pure and side-effect-free  
✅ Integrates existing modules cleanly  
✅ Typed and documented  
✅ 100% tested with Pytest  
✅ Works offline and with mocked time  
✅ No NVDA-specific logic

---

## 🔒 Exclusions

❌ No APScheduler or background threads  
❌ No real-time `datetime.now()` usage  
❌ No file, speech, or NVDA API calls  
❌ No mutation of persisted state — return only new results

---

## 📌 Notes

This module acts as the **scheduler heartbeat**. It may be called:

- Periodically from an NVDA timer
- On NVDA startup or resume
- On user action to "run scheduler now"

But its behavior must always be **testable, predictable**, and **purely functional**.
