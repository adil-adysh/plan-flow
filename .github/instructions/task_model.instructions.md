---
applyTo: "addon/globalPlugins/planflow/task/task_model.py"
---

# Module Instructions — Task Model (v2)

This module defines the **core persistent models** for the PlanFlow scheduler system. These models must be logic-free, testable, and compatible with TinyDB.

---

## ✨ Goals

- Represent user-defined tasks, retry policies, preferences, and scheduling metadata
- Support recurrence, retries, and missed task recovery
- Enable time slot–based scheduling, per-day working hours, and per-task priorities
- Provide data for execution history, tracking, and conflict resolution

---

## 📦 Module Contents

Define the following models using `@dataclass(frozen=True, slots=True)`:

---

### ✅ `TaskDefinition`

A user-configured task template.

```python
@dataclass(frozen=True, slots=True)
class TaskDefinition:
    id: str
    title: str
    description: Optional[str]
    link: Optional[str]
    created_at: datetime
    recurrence: Optional[timedelta]
    retry_policy: RetryPolicy
    priority: Literal["low", "medium", "high"]
    preferred_slots: list[str]
````

* `preferred_slots` must match user-defined `Slot.id`s
* `priority` affects scheduling order (high-priority tasks are scheduled first)
* Must be serializable via `asdict()` for TinyDB

---

### ✅ `RetryPolicy`

Rules for retrying a failed or missed task.

```python
@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_retries: int
    retry_interval: Optional[timedelta]
    speak_on_retry: bool
```

* If `retry_interval` is None, retries are scheduled in next available user slot

---

### ✅ `TaskOccurrence`

A scheduled occurrence of a `TaskDefinition`.

```python
@dataclass(frozen=True, slots=True)
class TaskOccurrence:
    id: str
    task_id: str
    scheduled_for: datetime
```

---

### ✅ `TaskExecution`

Runtime state of an individual occurrence.

```python
@dataclass(frozen=True, slots=True)
class TaskExecution:
    occurrence_id: str
    state: Literal["pending", "done", "missed", "cancelled"]
    retries_remaining: int
    history: list[TaskEvent]
```

Must include:

* `@property def is_reschedulable() -> bool`
* `@property def retry_count() -> int`
* `@property def last_event_time() -> Optional[datetime]`

---

### ✅ `TaskEvent`

Append-only audit log entry for task execution history.

```python
@dataclass(frozen=True, slots=True)
class TaskEvent:
    event: Literal["triggered", "missed", "rescheduled", "completed"]
    timestamp: datetime
```

---

### ✅ `TimeSlot`

Represents a daily time window defined by the user.

```python
@dataclass(frozen=True, slots=True)
class TimeSlot:
    id: str
    label: str
    start_time: time
    end_time: time
```

---

### ✅ `WorkingHours`

Represents allowed working periods per day of week.

```python
@dataclass(frozen=True, slots=True)
class WorkingHours:
    day: Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    start_time: time
    end_time: time
```

These restrict when tasks may be scheduled.

---

## ⚙️ Constraints

* No logic beyond derived properties (`is_reschedulable`, etc.)
* JSON-serializable with `asdict()` and `datetime.isoformat()` for all times
* All models should be safely storable in TinyDB

---

## 📚 Requirements

### Type Annotations

* Use full type annotations on all fields and properties
* Use `Literal`, `Optional`, and `Union` where applicable
* Avoid any runtime-dependent fields (e.g. callbacks, I/O handles)

### Docstrings

Each class must include a Google-style docstring:

* Purpose and usage
* Field documentation (in `Attributes:` block)
* Usage examples (if needed)

---

## 🧪 Testing

Tests will be written in `tests/test_task_model.py`. All models must:

* Be instantiable with sample data
* Be serializable via `dataclasses.asdict`
* Validate derived property logic

---

## 🔒 Exclusions

❌ No scheduling, retry logic, or time computations
❌ No TinyDB access (just structure)
❌ No speech, file I/O, or NVDA dependencies

---

## ✅ Completion Criteria

✅ Models for task definition, retry, execution, slotting, and scheduling
✅ All types and docstrings present
✅ TinyDB-compatible and serializable
✅ Frozen, immutable, side-effect free
✅ 100% testable, type-safe, logic-light
✅ Passes Pyright (strict) + Ruff linting
