---
applyTo: "addon/globalPlugins/planflow/task/smart_scheduler_service.py"
---

# Module Instructions — Smart Scheduler Service (v2)

This module defines the real-time scheduling orchestrator for PlanFlow. It coordinates timers, detects missed executions, performs safe retries and recurrences, and respects all task and slot constraints.

---

## ✨ Goals

- Trigger `TaskOccurrence`s at their scheduled time using `threading.Timer`
- Prevent re-execution of already completed tasks
- Delegate to `TaskScheduler` for retry or recurrence
- Use `CalendarPlanner` to validate availability and enforce user constraints
- Log execution history using `ExecutionRepository`
- Recover tasks missed due to app suspension or system sleep using `RecoveryService`
- Maintain purity outside of real-time trigger logic
- Stay NVDA-independent and side-effect-free outside of its own scope

---

## 📦 Class to Implement

### ✅ `SmartSchedulerService`

```python
class SmartSchedulerService:
    def start(self) -> None: ...
    def pause(self) -> None: ...
    def schedule_all(self) -> None: ...
    def schedule_occurrence(self, occ: TaskOccurrence) -> None: ...
    def check_for_missed_tasks(self) -> None: ...
````

---

## 🧩 Constructor Requirements

The class must be initialized with:

```python
def __init__(
    self,
    execution_repo: ExecutionRepository,
    scheduler: TaskScheduler,
    calendar: CalendarPlanner,
    recovery: RecoveryService,
    now_fn: Callable[[], datetime] = datetime.now
) -> None
```

Where:

* `execution_repo`: persistent backend for occurrences and execution history
* `scheduler`: core task recurrence/retry logic
* `calendar`: enforces working hours, slot validation, and caps
* `recovery`: handles missed tasks rescheduling
* `now_fn`: injectible clock for testability

Also initialize:

```python
self._timers: dict[str, threading.Timer] = {}
self._paused: bool = False
self._lock: threading.RLock = threading.RLock()
```

---

## ✅ Public Method Behavior

### `start(self) -> None`

* Sets `_paused = False`
* Cancels all existing timers
* Calls `schedule_all()`
* Calls `check_for_missed_tasks()`

---

### `pause(self) -> None`

* Sets `_paused = True`
* Cancels all timers via `_cancel_all_timers()`
* Prevents future scheduling until resumed

---

### `schedule_all(self) -> None`

* Cancels existing timers via `_cancel_all_timers()`
* Skips logic if `_paused = True`
* Retrieves all `TaskOccurrence`s
* Retrieves all completed executions (`state == "done"`)
* For each occurrence:

  * If `occ.scheduled_for > now_fn()` **and** `occ.id not in executed_ids`:

    * Call `schedule_occurrence(occ)`

---

### `schedule_occurrence(self, occ: TaskOccurrence) -> None`

#### Validation Logic:

1. Return early if paused
2. Fetch:

   * All scheduled occurrences (`list_occurrences()`)
   * All executed occurrences (`list_executions()` filtered for `state == "done"`)
3. Validate:

   * Skip if `occ.id in executed_ids`
   * Skip if `CalendarPlanner.is_slot_available(...)` returns `False`
4. If already scheduled (`occ.id in self._timers`), cancel old timer
5. Compute `delay = (occ.scheduled_for - now_fn()).total_seconds()`

#### Execution:

* If `delay <= 0`, call `_on_trigger(occ)` immediately
* Else:

  * Create a `threading.Timer(delay, self._on_trigger, args=(occ,))`
  * Mark it `daemon = True`
  * Start it and store in `self._timers[occ.id]`

---

### `check_for_missed_tasks(self) -> None`

* Skip if `_paused = True`
* Fetch all `TaskOccurrence`s
* Fetch all completed executions (`state == "done"`)
* For each `occ`:

  * Skip if `occ.id in executed_ids`
  * Compute `delta = (now_fn() - occ.scheduled_for).total_seconds()`
  * If `0 < delta <= _RECOVERY_GRACE_SECONDS`: call `_on_trigger(occ)`
  * If `delta > _RECOVERY_GRACE_SECONDS`: call `_trigger_recovery(occ)`

---

## 🔁 Internal Methods

### `_on_trigger(self, occ: TaskOccurrence) -> None`

1. Cancel and remove timer from `_timers` if exists
2. Add execution to `ExecutionRepository`:

   ```python
   exec = TaskExecution(
       id=generate_id(),
       task_id=occ.task_id,
       occurrence_id=occ.id,
       scheduled_for=occ.scheduled_for,
       actual_run=datetime.now(),
       state="done",
   )
   self._execution_repo.add_execution(exec)
   ```
3. Attempt to retry:

   ```python
   retries_remaining = max(0, occ.retry_count - 1)
   retry_occ = self._scheduler.reschedule_retry(occ, policy, now_fn(), ...)
   if retry_occ:
       self.schedule_occurrence(retry_occ)
       return
   ```
4. Attempt recurrence (if no retry occurred):

   ```python
   task = self._execution_repo.get_task(occ.task_id)
   if task and task.recurrence:
       next_occ = self._scheduler.get_next_occurrence(task, now_fn(), ...)
       if next_occ:
           self.schedule_occurrence(next_occ)
   ```

---

### `_trigger_recovery(self, occ: TaskOccurrence) -> None`

* Fetch:

  ```python
  all_executions = self._execution_repo.list_executions()
  all_occurrences = {o.id: o for o in self._execution_repo.list_occurrences()}
  all_tasks = {t.id: t for t in self._execution_repo.list_tasks()}
  ```
* Call:

  ```python
  new_occs = self._recovery.recover_missed_occurrences(
      executions=all_executions,
      occurrences=all_occurrences,
      tasks=all_tasks,
      now=now_fn(),
      calendar=self._calendar,
      scheduled_occurrences=list(all_occurrences.values()),
      working_hours=self._calendar.working_hours,
      slot_pool=self._calendar.slot_pool,
      max_per_day=self._calendar.max_per_day
  )
  for o in new_occs:
      self.schedule_occurrence(o)
  ```

---

### `_cancel_all_timers(self) -> None`

* Cancel all existing `threading.Timer`s in `self._timers`
* Clear the dictionary

---

## 📚 Additional Rules

* Maintain a constant:

  ```python
  _RECOVERY_GRACE_SECONDS: int = 30
  ```
* Use only `datetime.now()` via `now_fn()`
* Do not mutate shared collections
* Do not use logging, print, NVDA APIs, or I/O

---

## 🧪 Testing Guidelines

Tests must live in `tests/test_smart_scheduler_service.py`.

### Scenarios to Cover:

| Scenario                   | Expectation                       |
| -------------------------- | --------------------------------- |
| Task due immediately       | `_on_trigger` called directly     |
| Future task scheduled      | Timer created and fires correctly |
| Task already executed      | Not rescheduled                   |
| Slot invalid               | Skipped                           |
| Task missed < grace        | Triggered immediately             |
| Task missed > grace        | Delegated to recovery             |
| Retry returned             | New task scheduled                |
| Recurrence returned        | New task scheduled                |
| Pause prevents timers      | No timers created                 |
| Resume restarts scheduling | Timers recreated                  |

Use:

* `freezegun` for `now_fn`
* `threading.Event` to mock timer behavior
* Mocked `ExecutionRepository`, `TaskScheduler`, `CalendarPlanner`, `RecoveryService`

---

## ✅ Completion Checklist

✅ Fully typed with Python 3.11+ syntax
✅ Integrates all dependencies properly
✅ Fully supports retry + recurrence
✅ Ignores pinned-time during recovery
✅ Gracefully handles pause/resume
✅ Idempotent and race-free
✅ Pure outside of `datetime.now()`
✅ Fully unit-tested with mocks
✅ Passes `ruff check` and `pyright --verifytypes` in strict mode
✅ No NVDA, UI, I/O, or logging side effects
