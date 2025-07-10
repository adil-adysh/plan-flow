---
applyTo: "addon/globalPlugins/planflow/task/task_model.py"
---

# Module Instructions — Task Model

This module defines the **core data models** used by the PlanFlow task scheduler. These models represent the structure and state of scheduled tasks, retries, and user-defined timing preferences. They must remain **pure**, **testable**, and **JSON-serializable** for TinyDB.

---

## ✨ Goals

- Represent tasks, retries, time slots, and execution status
- Enable per-day working hours and named time slots
- Track execution lifecycle with event history
- Support user-defined pinned scheduling time via `TaskOccurrence`
- Avoid business logic — only data structure and derived properties
- Fully decouple from NVDA and external I/O

---

## 📦 Data Models to Implement

### ✅ `TaskDefinition`

Represents a user-defined task.

- `id: str`
- `title: str`
- `description: Optional[str]`
- `link: Optional[str]` — local file or URL
- `created_at: datetime`
- `recurrence: Optional[timedelta]`
- `priority: Literal["low", "medium", "high"]`
- `preferred_slots: list[str]` — names of `TimeSlot`s the task prefers
- `retry_policy: RetryPolicy`

---

### ✅ `RetryPolicy`

Defines the user's configuration for retrying missed tasks.

- `max_retries: int`

✅ Note: No retry interval or speech flags — retries are handled by re-scheduling in future valid time slots.

---

### ✅ `TaskOccurrence`

Represents a scheduled instance of a task.

- `id: str`
- `task_id: str`
- `scheduled_for: datetime`
- `slot_name: Optional[str]` — name of the time slot used for this occurrence
- `pinned_time: Optional[datetime]` — user-requested exact datetime (must be validated before use)

---

### ✅ `TaskExecution`

Tracks the runtime execution of a `TaskOccurrence`.

- `occurrence_id: str`
- `state: Literal["pending", "done", "missed", "cancelled"]`
- `retries_remaining: int`
- `history: list[TaskEvent]`

With derived properties:

```python
@property
def is_reschedulable(self) -> bool: ...

@property
def retry_count(self) -> int: ...

@property
def last_event_time(self) -> Optional[datetime]: ...
````

---

### ✅ `TaskEvent`

A log entry in a task’s execution lifecycle.

* `event: Literal["triggered", "missed", "rescheduled", "completed"]`
* `timestamp: datetime`

---

### ✅ `TimeSlot`

Represents a named time window for task delivery.

* `name: str` — must match values used in `preferred_slots`
* `start: time`
* `end: time`

---

### ✅ `WorkingHours`

Defines allowed scheduling hours per weekday.

* `day: Literal["monday", ..., "sunday"]`
* `start: time`
* `end: time`
* `allowed_slots: list[str]` — names of `TimeSlot`s allowed on that day

---

## ⚙️ Constraints

* Use `@dataclass(frozen=True, slots=True)` for all models
* All models must be **pure** and **side-effect free**
* All fields must be JSON-serializable
* Datetimes are timezone-naive (for now)
* Avoid nested logic or complex method bodies

---

## 📚 Requirements

### Type Annotations

* Use full type hints for all fields and return values
* Use Python 3.11+ syntax: `str | None` instead of `Optional[str]`, `int | str` instead of `Union[int, str]`, etc.
* Use `Literal`, `list[...]` as needed
* Prefer immutability where possible

> **Note:** Do not use legacy `Optional[...]` or `Union[...]` syntax.

### Docstrings

All classes and methods must use **Google-style** docstrings to describe:

* Purpose
* Parameters and their types
* Return values (if applicable)

---

## 🧪 Testing

All models must support unit testing via:

* Manual instantiation in `pytest`
* Serialization with `dataclasses.asdict(...)`
* Derived properties tested in isolation
* Tests located in `tests/test_task_model.py`

---

## 🔒 Exclusions

❌ No NVDA APIs
❌ No scheduling logic
❌ No time lookups or `datetime.now()`
❌ No I/O, storage, or real-time side effects

---

## ✅ Completion Criteria

✅ All models defined with frozen dataclasses and `slots=True`
✅ Fully type-annotated and documented
✅ Compatible with TinyDB
✅ Priority and preferred slots included
✅ Retry interval dropped in favor of time-slot-based retry
✅ `pinned_time` optionally supported in `TaskOccurrence`
✅ All fields serializable and cleanly structured
✅ Passes Pyright (strict) and Ruff
