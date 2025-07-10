---
applyTo: "tests/**/*.py"
---

# Testing Instructions — PlanFlow Add-on

These guidelines apply to **all test files** for the PlanFlow NVDA add-on. Tests validate the logic and data models defined in `addon/globalPlugins/planflow/`, and must be **pure, fast, and NVDA-independent**.

---

## ✅ Goals

- Ensure all logic is covered with meaningful unit tests
- Keep all tests NVDA-independent and side-effect-free
- Validate type safety, recurrence, retries, recovery, and storage
- Provide clear fixtures, parameterization, and input coverage

---

## 🧪 Pytest Rules

- All test files must start with: `test_*.py`
- Each test function must start with `test_`
- Group related tests in classes or modules (without `self`)
- Use [`pytest.mark.parametrize`](https://docs.pytest.org/en/latest/example/parametrize.html) for edge case testing

---

## 🧱 Structure of Test Files

```python
# test_task_model.py

import pytest
from planflow.task.task_model import TaskDefinition

def test_create_task_with_defaults():
    task = TaskDefinition(...)
    assert task.title == "..."
````

Each test file must contain:

* Imports from the corresponding module
* At least one test per public function or property
* Parametrized tests where logic involves branches
* Coverage for error conditions (e.g., retry overflow)

---

## 🧪 Fixtures

### Guidelines

* Use `@pytest.fixture` for shared data (e.g. clocks, sample models)
* Keep fixtures stateless and isolated
* Use `tmp_path` for temporary file/directory tests

### Example Fixture

```python
@pytest.fixture
def sample_retry_policy() -> RetryPolicy:
    return RetryPolicy(max_retries=3, retry_interval=timedelta(minutes=5), speak_on_retry=True)
```

---

## 🚫 NVDA & I/O Rules

Tests must:

* **Not import or use NVDA APIs**
* **Not read or write real files**
* **Not rely on `datetime.now()` or real clocks**
* **Not include speech output or UI interaction**

Use dependency injection (`now: datetime`) and test with simulated time.

---

## 🔁 Behavior to Test by File

| Module                    | Test Requirements                                               |
| ------------------------- | --------------------------------------------------------------- |
| `task_model.py`           | Dataclass correctness, property logic, serialization integrity  |
| `scheduler_service.py`    | Due/missed detection, recurrence, retry logic                   |
| `recovery_service.py`     | Missed task rescheduling, retry exhaustion, recurrence behavior |
| `calendar_planner.py`     | Per-day limits, slot availability, next valid day computation   |
| `execution_repository.py` | CRUD operations with TinyDB, MemoryStorage support              |

---

## ✅ Completion Criteria for Test Files

Each test file must:

* Contain ≥ 90% branch coverage for its target module
* Be compatible with:

  * `pytest`
  * `pyright --verifytypes`
  * `ruff check`
* Run independently (no global dependencies)
* Include meaningful test case names and assertions

---

## 🛠 Recommended Tools

| Tool     | Purpose              | VS Code Extension ID    |
| -------- | -------------------- | ----------------------- |
| Pytest   | Unit testing         | `ms-python.python`      |
| Coverage | Coverage analysis    | `pytest-cov` (CLI only) |
| Pyright  | Type safety checking | `ms-pyright.pyright`    |

---

## 📂 Test Directory Layout

```text
tests/
├── test_task_model.py
├── test_scheduler_service.py
├── test_recovery_service.py
├── test_calendar_planner.py
└── test_execution_repository.py
```

Each test file should mirror its implementation file in name and scope.

---

## ✅ Test Output Format

Use **assertions** over `print()`
Prefer `assert obj == expected` to hardcoded values
Avoid catching exceptions unless testing failures

---

## 🧼 Bonus Practices

* Use `freezegun` or `fake_clock` patterns if mocking time
* Parameterize tests that compare recurrence intervals, retry counts, etc.
* Use `dataclasses.asdict()` for round-trip serialization checks

---

## Linting & Type Checking

All tests must pass:

* `ruff check tests/`
* `pyright --verifytypes` (in strict mode)
