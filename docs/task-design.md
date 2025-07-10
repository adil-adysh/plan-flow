# 📝 PlanFlow Task Scheduler — Design Document

## 📌 Goal

Design and implement a **fully local**, **reliable**, and **testable** task scheduling system as part of the PlanFlow NVDA add-on.

It must support:

* Recurring and one-time tasks
* Missed task recovery (e.g., NVDA was off)
* Retry logic with configurable limits
* Per-day task capacity constraint
* Task trigger events (e.g., NVDA speech)
* Full testability with no real-time dependency

---

## 🧱 High-Level Architecture

```
+---------------------+
| NVDA Frontend       |
|  (TaskRunner, Output)|
+----------+----------+
           |
           v
+----------+----------+
| Application Service |
| (PlanFlowEngine)    |
+----------+----------+
           |
           v
+-----------------------------+
| Pure Logic Layer           |
| (Scheduler, RecoveryEngine)|
+-----------------------------+
           |
           v
+-----------------------------+
| Persistence Layer          |
| (Repos: Task, Instance,    |
| Execution, CalendarIndex)  |
+-----------------------------+
           |
           v
+-----------------------------+
| Storage (TinyDB)           |
+-----------------------------+
```

---

## 1. ✅ Domain Models


### 1.1 `TaskDefinition`

Represents the **user-configured** task template.

```python
@dataclass(frozen=True, slots=True)
class TaskDefinition:
    id: str
    title: str
    description: str | None
    link: str | None
    created_at: datetime
    recurrence: object | None  # typically timedelta, or None
    priority: Literal["low", "medium", "high"]
    preferred_slots: list[str]  # names of preferred TimeSlots
    retry_policy: RetryPolicy
```

---


### 1.2 `TaskOccurrence`

Generated from a `TaskDefinition`—this represents one **scheduled due time**.

```python
@dataclass(frozen=True, slots=True)
class TaskOccurrence:
    id: str
    task_id: str
    scheduled_for: datetime
    slot_name: str | None  # name of the time slot used for this occurrence
```

---


### 1.3 `TaskExecution`

Tracks **runtime state** of a scheduled task occurrence.

```python
@dataclass(frozen=True, slots=True)
class TaskExecution:
    occurrence_id: str
    state: Literal["pending", "done", "missed", "cancelled"]
    retries_remaining: int
    history: list[TaskEvent]

    @property
    def is_reschedulable(self) -> bool: ...
    @property
    def retry_count(self) -> int: ...
    @property
    def last_event_time(self) -> datetime | None: ...
```

---


### 1.4 `RetryPolicy`

Defines task-specific retry behavior.

```python
@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_retries: int
```

---


### 1.5 `TaskEvent`

Immutable log entry. Used in `TaskExecution.history`.

```python
@dataclass(frozen=True, slots=True)
class TaskEvent:
    event: Literal["triggered", "missed", "rescheduled", "completed"]
    timestamp: datetime
```
### 1.6 `TimeSlot`

Represents a named time window for task delivery.

```python
@dataclass(frozen=True, slots=True)
class TimeSlot:
    name: str
    start: time
    end: time
```

### 1.7 `WorkingHours`

Defines allowed scheduling hours per weekday.

```python
@dataclass(frozen=True, slots=True)
class WorkingHours:
    day: Literal["monday", ..., "sunday"]
    start: time
    end: time
    allowed_slots: list[str]
```

---

## 2. ⚙️ Pure Logic Layer


### 2.1 `TaskScheduler`

Handles due checks, recurrence generation, retry/rescheduling, and slot-aware scheduling.

```python
class TaskScheduler:
    def is_due(self, occurrence: TaskOccurrence, now: datetime) -> bool
    def is_missed(self, occurrence: TaskOccurrence, now: datetime) -> bool
    def should_retry(self, execution: TaskExecution) -> bool
    def get_next_occurrence(
        self,
        task: TaskDefinition,
        from_time: datetime,
        calendar: CalendarPlanner,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        slot_pool: list[TimeSlot],
        max_per_day: int
    ) -> TaskOccurrence | None
    def reschedule_retry(
        self,
        occurrence: TaskOccurrence,
        policy: RetryPolicy,
        now: datetime,
        calendar: CalendarPlanner,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        slot_pool: list[TimeSlot],
        max_per_day: int
    ) -> TaskOccurrence | None
```

---


### 2.2 `RecoveryService`

Handles tasks missed while NVDA was off, using CalendarPlanner and TaskScheduler.

```python
class RecoveryService:
    def recover_missed_occurrences(
        self,
        executions: list[TaskExecution],
        occurrences: dict[str, TaskOccurrence],
        tasks: dict[str, TaskDefinition],
        now: datetime,
        calendar: CalendarPlanner,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        slot_pool: list[TimeSlot],
        max_per_day: int
    ) -> list[TaskOccurrence]
```

---


### 2.3 `CalendarPlanner`

Enforces working hours, slot preferences, and per-day task limits. Computes valid scheduling windows and next available slots.

```python
class CalendarPlanner:
    def is_slot_available(
        self,
        proposed_time: datetime,
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        max_per_day: int,
        slot_pool: list[TimeSlot] | None = None
    ) -> bool
    def next_available_slot(
        self,
        after: datetime,
        slot_pool: list[TimeSlot],
        scheduled_occurrences: list[TaskOccurrence],
        working_hours: list[WorkingHours],
        max_per_day: int,
        priority: int | None = None
    ) -> datetime | None
    # Only searches up to 7 days ahead for available slots
```

---

## 3. 💾 Persistence Layer

TinyDB-backed. Split responsibilities for clarity.


### 3.1 `ExecutionRepository`

Handles storage of user-configured tasks, occurrences, and executions using TinyDB.

```python
class ExecutionRepository:
    def add_task(self, task: TaskDefinition) -> None
    def get_task(self, task_id: str) -> TaskDefinition | None
    def list_tasks(self) -> list[TaskDefinition]
    def add_occurrence(self, occ: TaskOccurrence) -> None
    def list_occurrences(self) -> list[TaskOccurrence]
    def add_execution(self, exec: TaskExecution) -> None
    def list_executions(self) -> list[TaskExecution]
```

---



---


## 4. 🧪 Testing Strategy

All logic is designed to be **pure**, **deterministic**, and **testable**. All models and logic are covered by pytest-based unit tests, with edge cases for slot search, per-day caps, and missed/retry logic. No NVDA or real-time dependencies are present in tests.

### Tools

* `pytest`
* `freezegun` or `FakeClock` for time mocking
* In-memory TinyDB for persistence testing
* NVDA side effects fully mocked

---

### Example Test Case: Missed Task Recovery

```python
def test_recovery_reschedules_task():
    # Arrange
    fake_clock = FakeClock(datetime(2025, 7, 10, 10, 0))
    task = TaskDefinition(..., recurrence=timedelta(days=1), ...)
    occurrence = TaskOccurrence(scheduled_for=datetime(2025, 7, 10, 8, 0))
    execution = TaskExecution(state="pending", retries_remaining=2, ...)

    # Act
    scheduler = TaskScheduler(clock=fake_clock)
    recovery = RecoveryEngine()
    new_occurrences = recovery.recover_missed_tasks(...)

    # Assert
    assert len(new_occurrences) == 1
    assert new_occurrences[0].scheduled_for > fake_clock.now()
```

---

## 5. 🔊 NVDA Side Effect Layer

### `TaskRunner`

Executes a task: speaks, marks done, etc.

```python
class TaskRunner:
    def run(task_execution: TaskExecution)
```

---

### `NVDAOutput`

Handles speech and optional braille.

```python
class NVDAOutput:
    def speak(text: str)
```

✅ You mock this layer in tests.

---

## 6. 🧭 Boot Flow (PlanFlow Engine)

```python
class PlanFlowEngine:
    def on_nvda_startup():
        - Load tasks, occurrences, executions
        - Recover missed tasks via `RecoveryEngine`
        - Reschedule tasks via `TaskScheduler`
        - Update TinyDB
```

---

## ✅ Summary Table

| Component         | Testable   | Real-time Independent | Decoupled |
| ----------------- | ---------- | --------------------- | --------- |
| Domain Models     | ✅          | ✅                     | ✅         |
| Logic Layer       | ✅          | ✅                     | ✅         |
| Persistence       | ✅          | ✅                     | ✅         |
| NVDA Side Effects | ✅ (mocked) | ✅                     | ✅         |

---


## 📦 Recommended File Structure

```
planflow/
├── task/
│   ├── task_model.py
│   ├── calendar_planner.py
│   ├── scheduler_service.py
│   ├── recovery_service.py
│   ├── execution_repository.py
├── nvda_adapter/
│   ├── runner.py
│   └── output.py
├── core/
│   ├── engine.py
│   └── clock.py
└── tests/
```

---

## 🏁 Implementation Order (Recommended)

1. ✅ Implement `TaskDefinition`, `TaskOccurrence`, `TaskExecution` (models)
2. ✅ Implement `Scheduler`, `RetryPolicy`, `RecurrencePolicy` (logic)
3. ✅ Implement `RecoveryEngine` and `CalendarCapacityPlanner`
4. ✅ Write test cases with `FakeClock`
5. ✅ Build repositories for TinyDB
6. ✅ Integrate with `PlanFlowEngine` + NVDA speech layer
