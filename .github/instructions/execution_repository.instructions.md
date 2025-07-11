---
applyTo: "addon/globalPlugins/planflow/task/execution_repository.py"
---

# Module Instructions — Execution Repository

This module defines a **TinyDB-backed storage layer** for managing task-related data: task definitions, scheduled occurrences, and execution history. It provides clean, testable APIs to interact with persistent state.

---

## ✨ Goals

- Persist and retrieve `TaskDefinition`, `TaskOccurrence`, and `TaskExecution`
- Provide type-safe, logic-free CRUD interfaces
- Remain decoupled from scheduling, retry, or UI logic
- Allow seamless in-memory use for unit testing

---

## 📦 Class to Implement

### ✅ `ExecutionRepository`

A single class for storage access.

#### Public Methods:

```python
class ExecutionRepository:

    def add_task(self, task: TaskDefinition) -> None: ...
    def get_task(self, task_id: str) -> Optional[TaskDefinition]: ...
    def list_tasks(self) -> list[TaskDefinition]: ...

    def add_occurrence(self, occ: TaskOccurrence) -> None: ...
    def list_occurrences(self) -> list[TaskOccurrence]: ...

    def add_execution(self, exec: TaskExecution) -> None: ...
    def list_executions(self) -> list[TaskExecution]: ...

    def delete_task_and_related(self, task_id: str) -> None: ...
```

---

## ⚙️ Constraints

* Use `TinyDB` with `.table("tasks")`, `.table("occurrences")`, `.table("executions")`
* Store only `@dataclass` values converted via `asdict()`
* Handle ID-based uniqueness but allow overwrites (idempotency)
* Store timestamps as ISO strings (using `datetime.isoformat()`), not native `datetime` objects, for TinyDB compatibility
* No logic — just persistence and retrieval
* `delete_task_and_related` must remove the task, all related occurrences, and all executions for those occurrences (cascade delete)

---

## 🧩 Requirements

### Input Types

* Must accept only typed models (`TaskDefinition`, `TaskOccurrence`, `TaskExecution`)
* Must validate uniqueness by `id` field in each model

### Output Types

* Return deserialized instances from JSON-compatible dicts
* Type signatures must match return values exactly
* `delete_task_and_related` returns `None` and removes all relevant records

---

##  Type Annotations

* All arguments and return types must be fully annotated
* Use Python 3.11+ syntax: `str | None` instead of `Optional[str]`, `int | str` instead of `Union[int, str]`, etc.
* Use `list[...]`, `-> None`, etc.
* Avoid use of `Any` or `dict` in public interfaces

> **Note:** Do not use legacy `Optional[...]` or `Union[...]` syntax.

---

## 📝 Docstrings

Each method must include a Google-style docstring with:

* Purpose
* Parameters and types
* Return values and format
* Any side effects (e.g. overwrite, in-place update)

For `delete_task_and_related`:
* Purpose: Remove a task and all related occurrences and executions by `task_id`.
* Parameters: `task_id` (str): The ID of the TaskDefinition to delete.
* Returns: None. Removes the task, its occurrences, and executions from the database.
* Side effects: Removes all records from 'tasks', 'occurrences', and 'executions' tables related to the given `task_id`.

---

## 🧪 Testing

All storage operations must be testable.

Write tests in `tests/test_execution_repository.py` with:

* `TinyDB(storage=MemoryStorage)` as test backend
* Test each method independently
* Include roundtrip tests (store → read → compare)
* Confirm model compatibility and ID consistency

---

## 🔒 Exclusions

❌ No scheduling logic
❌ No NVDA APIs
❌ No time logic
❌ No cross-table joins
❌ No schema migration logic

---

## ✅ Completion Criteria

✅ Fully typed and documented methods
✅ Stores and retrieves each model correctly
✅ 100% test coverage in isolated tests
✅ All I/O confined to TinyDB
✅ Works with both real file and memory backends
✅ Ruff + Pyright clean
✅ Logic-free and stable
