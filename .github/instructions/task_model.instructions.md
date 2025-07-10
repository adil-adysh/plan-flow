---
applyTo: "addon/globalPlugins/planflow/task/task_model.py"
---

# Module Instructions — Task Model

This module defines the **core data models** used by the PlanFlow NVDA add-on’s task scheduler. These models represent persistent data structures and must remain **logic-free, testable, and serializable**.

---

## ✨ Goals

- Represent user-defined tasks and runtime state
- Support recurrence, retries, and missed task recovery
- Provide structure for execution tracking and future extensibility
- Remain decoupled from scheduling logic, time functions, and I/O

---

## 📦 Module Contents

Implement the following classes:

### ✅ TaskDefinition

Represents a user-configured task.

- `id: str` — unique identifier
- `title: str`
- `description: Optional[str]`
- `link: Optional[str]` — may point to a URL or file path
- `created_at: datetime`
- `recurrence: Optional[timedelta]`
- `retry_policy: RetryPolicy`

---

### ✅ RetryPolicy

Defines behavior when a task is missed or fails.

- `max_retries: int`
- `retry_interval: timedelta`
- `speak_on_retry: bool`

---

### ✅ TaskOccurrence

Represents a scheduled instance of a task.

- `id: str`
- `task_id: str`
- `scheduled_for: datetime`

---

### ✅ TaskExecution

Tracks the runtime status of a task occurrence.

- `occurrence_id: str`
- `state: Literal["pending", "done", "missed", "cancelled"]`
- `retries_remaining: int`
- `history: list[TaskEvent]`

Also implement utility methods:

- `@property def is_reschedulable() -> bool`
- `@property def retry_count() -> int`
- `@property def last_event_time() -> Optional[datetime]`

---

### ✅ TaskEvent

Append-only event log used in `history`.

- `event: Literal["triggered", "missed", "rescheduled", "completed"]`
- `timestamp: datetime`

---

## ⚙️ Constraints

- All models must use `@dataclass` with `frozen=True`, `slots=True`
- Serialization must be compatible with TinyDB JSON (no binary/complex types)
- Time values must use `datetime` or `timedelta`
- Use `Literal`, `Optional`, and proper typing for all fields

---

## 📚 Requirements

### Type Annotations

- All classes and methods must include full, strict type hints
- Use `-> None` explicitly where applicable
- Prefer `Literal[...]` for enums over raw strings in logic

### Docstrings

Each class and method must have a Google-style or reST docstring explaining:

- Purpose
- Parameters
- Return values (if applicable)
- Example usage (if needed)

---

## ✅ Examples

### Class Skeleton with Type Annotations and Docstring

```python
@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Defines retry behavior for a task.

    Attributes:
        max_retries: Total number of retry attempts allowed.
        retry_interval: Time delay between retries.
        speak_on_retry: Whether NVDA should speak the task on retry.
    """
    max_retries: int
    retry_interval: timedelta
    speak_on_retry: bool = True
````

---

## 🧪 Testing

Although this file will not include test code, it **must** be structured so:

* Unit tests can construct each model easily
* You can serialize/deserialize models for TinyDB
* All derived properties can be verified via `pytest`

A test file `tests/test_task_model.py` will be created separately.

---

## 🔒 Exclusions

❌ No business logic (scheduling, retrying, etc.)
❌ No NVDA imports or APIs
❌ No file system or speech side effects
❌ No TinyDB-specific APIs — only standard JSON-serializable types

---

## ✅ Completion Criteria

✅ All five classes implemented with full annotations and docstrings
✅ All fields documented and testable
✅ Serialization confirmed for TinyDB
✅ No I/O, NVDA logic, or side effects
✅ Lint/Type check passes via Ruff + Pyright

---
