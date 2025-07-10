---
applyTo: "addon/globalPlugins/planflow/task/execution_repository.py"
---

# Module Instructions — Execution Repository

This module defines a **TinyDB-backed storage layer** for managing task-related data: definitions, scheduled occurrences, and execution history. It provides safe CRUD APIs for use by logic layers (scheduler, recovery, etc.).

---

## ✨ Goals

- Persist and retrieve `TaskDefinition`, `TaskOccurrence`, and `TaskExecution`
- Provide atomic, type-safe, and pure storage methods
- Fully decouple logic and storage concerns
- Enable isolated unit testing with in-memory or mock DB

---

## 📦 Module Contents

Implement a public class:

### ✅ `ExecutionRepository`

Backed by TinyDB, this manages all task-related records by `id`.

---

### Public Methods

```python
class ExecutionRepository:

    def add_task(self, task: TaskDefinition) -> None:
        """Store a new task definition."""

    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """Fetch a task by ID."""

    def list_tasks(self) -> list[TaskDefinition]:
        """Return all task definitions."""

    def add_occurrence(self, occ: TaskOccurrence) -> None:
        """Store a task occurrence."""

    def list_occurrences(self) -> list[TaskOccurrence]:
        """Return all known occurrences."""

    def add_execution(self, exec: TaskExecution) -> None:
        """Store a new task execution record."""

    def list_executions(self) -> list[TaskExecution]:
        """Return all executions."""
````

---

## ⚙️ Constraints

* All data must be JSON-serializable via `dataclasses.asdict()`
* Must support pluggable storage (file-based or in-memory for testing)
* Keep logic pure: no side effects outside TinyDB ops
* Handle record collisions gracefully (idempotency where useful)

---

## 📚 Requirements

### TinyDB

Use the following structure:

| Table Name      | Stores           |
| --------------- | ---------------- |
| `"tasks"`       | `TaskDefinition` |
| `"occurrences"` | `TaskOccurrence` |
| `"executions"`  | `TaskExecution`  |

Use `.table("tasks")` etc. for organization.

---

### Type Annotations

* All methods must include full type hints
* Use `Optional[...]`, `-> None`, and `list[Model]` signatures

---

### Docstrings

Each method and class must include docstrings:

* Purpose of the method
* Parameter definitions
* Return value
* Side-effect summary

---

## 🧪 Testing

Write tests in `tests/test_execution_repository.py` with:

* `MemoryStorage` (in-memory DB backend)
* Pytest fixtures to set up and tear down DB state
* Unit tests for add/get/list across all types
* Serialization/deserialization coverage for model integrity

---

## 🔒 Exclusions

❌ No business logic (scheduling, retries)
❌ No NVDA API access
❌ No direct JSON file management (TinyDB handles it)
❌ No `print()`, logging, or speech output

---

## ✅ Completion Criteria

✅ All CRUD methods implemented for 3 entities
✅ Fully typed and documented
✅ Compatible with TinyDB and MemoryStorage
✅ No NVDA or scheduling logic mixed in
✅ 100% testable via `pytest`
✅ Lint/type-check clean (Ruff + Pyright strict)
