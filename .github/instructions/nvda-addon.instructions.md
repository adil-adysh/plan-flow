---
applyTo: "**"
---

# PlanFlow Add-on Development Instructions

These are project-wide guidelines to help AI and humans generate consistent, testable, and portable code for the PlanFlow NVDA add-on. The add-on is written in standard Python and must remain compatible with non-NVDA environments unless explicitly required.

---

## General Principles

- Write code in **standard Python** (no NVDA-specific APIs unless explicitly required).
- All logic must be **testable independently of NVDA**.
- Prioritize **readability**, **modularity**, and **portability**.
- Avoid runtime logic in constructors that depends on I/O or global state.

---

## File Structure & Naming

- Core logic: `addon/globalPlugins/planflow/`
- Unit tests: `tests/`
- File naming:
  - `*_model.py` for data structures
  - `*_manager.py`, `*_service.py` for behavior
  - `test_*.py` for test files
- Organize related modules into folders (`task/`, `utils/`, etc.)

---

## NVDA Compatibility Rules

- Core logic must not use NVDA APIs.
- NVDA-specific code (e.g. speech, UI hooks) must be isolated in `nvda_adapter/`.
- Unit tests must not import NVDA modules.
- Mock NVDA behavior with clear `# NVDA MOCK:` comments when absolutely necessary.

---

## Code Formatting, Style & Structure

- Use [Ruff](https://docs.astral.sh/ruff/) for formatting, linting, and import sorting.
- Use [Pyright](https://github.com/microsoft/pyright) in **strict mode** for type checking.
- Follow **PEP8** and **PEP257** style and docstring conventions.

### Naming Conventions

| Entity        | Style         | Example              |
|---------------|---------------|----------------------|
| Function      | `snake_case`  | `get_due_tasks()`    |
| Class         | `PascalCase`  | `ScheduledTask`      |
| Constant      | `ALL_CAPS`    | `DEFAULT_TIMEOUT`    |
| Private Field | `_underscore` | `_callback`          |

---

## Type Annotations — Required

All implementation code **must** include full type annotations:

- Every **function and method** must specify parameter and return types.
- Use `-> None` explicitly when a function returns nothing.
- Use `Optional[...]` where `None` is a valid value.
- Use `Literal`, `Union`, `TypedDict`, or `Annotated` as needed for clarity.

---

## Docstrings — Required

All modules, classes, methods, and functions must include **meaningful docstrings**:

| Element      | Docstring Requirement                            |
|--------------|---------------------------------------------------|
| Module       | At the top of every `.py` file                    |
| Class        | Summarize its purpose and usage                   |
| Function     | Describe what it does, parameters, and returns    |
| Method       | Same as function (document `self`-based behavior) |

Use **Google-style**, **reST**, or **NumPy-style** consistently.

### Example — Function with Type Hints and Docstring

```python
def calculate_priority(deadline: int, weight: float) -> float:
    """Calculate task priority based on deadline and weight.

    Args:
        deadline: UNIX timestamp of the task deadline.
        weight: Importance multiplier (1.0 = neutral).

    Returns:
        A float score representing the task's priority.
    """
    return weight / (deadline + 1)
````

---

## Dataclass Guidelines

* Use `@dataclass` for structured data.
* Favor immutability: `frozen=True` where appropriate.
* Use `slots=True` for memory efficiency.
* Runtime-only or callback fields must:

  * be prefixed with `_`
  * use `repr=False`, `compare=False`

---

## Testing & Environment

* Use [pytest](https://docs.pytest.org/) for all unit tests.
* Test files live in `tests/` and are named `test_*.py`
* Tests must:

  * run in standard Python (no NVDA dependencies)
  * avoid global state and side effects
  * use fixtures for setup

### Example — Typed Pytest Fixture

```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    """Create a sample file with default content."""
    file = tmp_path / "sample.txt"
    file.write_text("Hello")
    return file
```

---

## Tooling & Automation

Configure these tools and enforce via CI and VS Code:

| Tool    | Purpose              | VS Code Extension ID |
| ------- | -------------------- | -------------------- |
| Ruff    | Linting + formatting | `charliermarsh.ruff` |
| Pyright | Type checking        | `ms-pyright.pyright` |
| Pytest  | Unit testing         | `ms-python.python`   |

```jsonc
// .vscode/settings.json (recommended)
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.analysis.typeCheckingMode": "strict",
  "ruff.enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true,
    "source.organizeImports": true
  },
  "github.copilot.advanced": {
    "enableInstructionFiles": true
  }
}
```

---

## AI Code Generation Guidelines

When using Copilot, Copilot Chat, or other AI:

* **Always** include:

  * Type annotations
  * Docstrings for classes, functions, methods, modules
* Do not use NVDA-specific APIs unless explicitly required
* Prefer pure Python examples
* Structure code for testability
* Use `pytest` style and test structure as outlined

---

## Example — Minimal Valid Python Module

```python
"""Module for handling scheduled task logic."""

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ScheduledTask:
    """A scheduled task with a due time."""
    name: str
    due_time: int

    def is_due(self, current_time: int) -> bool:
        """Check if the task is due at the given time.

        Args:
            current_time: UNIX timestamp to compare against due time.

        Returns:
            True if the task is due, else False.
        """
        return current_time >= self.due_time
```

---

## Behavior Guidelines

* Avoid complex nesting; favor small, focused functions.
* Separate concerns clearly (data, logic, IO/adapters).
* When in doubt, choose **readability** and **clarity**.

---
