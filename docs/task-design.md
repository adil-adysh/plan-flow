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
class TaskDefinition(BaseModel):
    id: str
    title: str
    description: Optional[str]
    link: Optional[str]
    created_at: datetime
    recurrence: Optional[timedelta]
    retry_policy: RetryPolicy
```

---

### 1.2 `TaskOccurrence`

Generated from a `TaskDefinition`—this represents one **scheduled due time**.

```python
class TaskOccurrence(BaseModel):
    id: str
    task_id: str
    scheduled_for: datetime
```

---

### 1.3 `TaskExecution`

Tracks **runtime state** of a scheduled task occurrence.

```python
class TaskExecution(BaseModel):
    occurrence_id: str
    state: Literal["pending", "done", "missed", "cancelled"]
    retries_remaining: int
    history: List[TaskEvent]
```

---

### 1.4 `RetryPolicy`

Defines task-specific retry behavior.

```python
class RetryPolicy(BaseModel):
    max_retries: int
    retry_interval: timedelta
    speak_on_retry: bool = True
```

---

### 1.5 `TaskEvent`

Immutable log entry. Used in `TaskExecution.history`.

```python
class TaskEvent(BaseModel):
    event: Literal["triggered", "missed", "completed", "rescheduled"]
    timestamp: datetime
```

---

## 2. ⚙️ Pure Logic Layer

### 2.1 `TaskScheduler`

Handles due checks, recurrence generation, retry/rescheduling.

```python
class TaskScheduler:
    def is_due(self, occurrence: TaskOccurrence, now: datetime) -> bool
    def get_next_occurrence(self, task: TaskDefinition, from_time: datetime) -> TaskOccurrence
    def should_reschedule(self, execution: TaskExecution) -> bool
```

---

### 2.2 `RecoveryEngine`

Handles tasks missed while NVDA was off.

```python
class RecoveryEngine:
    def recover_missed_tasks(
        self,
        now: datetime,
        executions: list[TaskExecution],
        scheduler: TaskScheduler,
    ) -> list[TaskOccurrence]
```

---

### 2.3 `CalendarCapacityPlanner`

Limits tasks per day.

```python
class CalendarCapacityPlanner:
    def can_schedule(self, date: datetime.date) -> bool
    def register(self, occurrence: TaskOccurrence)
    def find_next_available_day(self, start: date) -> date
```

---

## 3. 💾 Persistence Layer

TinyDB-backed. Split responsibilities for clarity.

### 3.1 `TaskRepository`

Handles storage of user-configured tasks.

```python
class TaskRepository:
    def get_all(): list[TaskDefinition]
    def save(task: TaskDefinition)
```

---

### 3.2 `OccurrenceRepository`

Stores scheduled occurrences.

```python
class OccurrenceRepository:
    def get_all(): list[TaskOccurrence]
    def save(occurrence: TaskOccurrence)
```

---

### 3.3 `ExecutionRepository`

Stores execution state per occurrence.

```python
class ExecutionRepository:
    def get_all(): list[TaskExecution]
    def update(execution: TaskExecution)
```

---

### 3.4 `CalendarIndex`

Tracks how many tasks are scheduled per day.

```python
class CalendarIndex:
    def count(date: datetime.date) -> int
    def add(occurrence: TaskOccurrence)
```

---

## 4. 🧪 Testing Strategy

All logic is designed to be **pure**, **deterministic**, and **testable**.

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
├── models/
│   ├── definition.py
│   ├── occurrence.py
│   ├── execution.py
│   ├── policy.py
│   └── event.py
├── logic/
│   ├── scheduler.py
│   ├── recovery.py
│   └── planner.py
├── persistence/
│   ├── tasks.py
│   ├── occurrences.py
│   ├── executions.py
│   └── calendar.py
├── nvda/
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
