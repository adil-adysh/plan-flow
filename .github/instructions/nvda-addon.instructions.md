---
applyTo: "**"
---

# PlanFlow Add-on Development Instructions

These are project-wide guidelines to help AI generate consistent, testable, and portable code for the PlanFlow NVDA add-on. The add-on is written in standard Python and should remain compatible with non-NVDA environments unless explicitly required.

## General Principles

- Write code that runs in **standard Python** (no NVDA-specific APIs unless explicitly required).
- Prioritize **cross-platform portability** and readability.
- Assume all code should be **testable independently of NVDA**.

## Formatting and Style

- Use `ruff` for formatting and linting.
- Follow **PEP8** conventions.
- Use **type annotations** wherever meaningful.
- Keep imports sorted: stdlib, third-party, then local.

## Code Structure

- Use **`dataclass`** for structured data, and favor immutability when possible.
- Runtime-only attributes (e.g., callbacks) must be:
  - marked with `repr=False`, and
  - excluded from `__eq__` comparisons (`compare=False`).
- Avoid any logic inside `__init__` that depends on external systems (e.g., I/O, NVDA globals).

## Testing & Environment

- All code should be testable using **standard Python test frameworks** like `pytest`.
- Do not require NVDA to be installed for running unit tests.
- Prefer structured return values over `print()` or side effects.

## Implementing Test Cases with pytest

When adding or updating test cases for PlanFlow:

- Place all test files in the `tests/` directory. Name files as `test_*.py`.
- Use standard `pytest` conventions: test functions should be named `test_*` and test classes should be named `Test*` (no `__init__` method required).
- Import the module to be tested using relative imports (e.g., `from addon.globalPlugins.planflow.task import model`).
- Each test should be independent and not rely on NVDA or external state.
- Use assertions to check expected behavior. Avoid `print()` statements.
- Prefer small, focused test functions over large, complex ones.
- Use fixtures for setup/teardown if needed (see `pytest` docs).
- Add docstrings to test functions and classes to describe their purpose.
- Add useful comments explaining the purpose of each test case, especially where the intent or logic may not be obvious.
- All test functions, fixtures, and helper functions must have explicit type annotations for parameters and return types.
- Add type annotations for pytest fixture parameters (e.g., `tmp_path: Path`).
- If a class defines `__init__`, always call `super().__init__()` for linter and type checker compliance.
- Use `type: ignore` comments only when necessary (e.g., accessing protected members for testability), and always add a comment explaining why.
- Import all types used in annotations (e.g., `Path` from `pathlib`).
- Ensure all test files pass strict linting and type checking (e.g., Ruff, Pyright in strict mode).
- Add useful comments explaining the purpose of each test case, especially where the intent or logic may not be obvious.

**Example:**

```python
import pytest
from addon.globalPlugins.planflow.task.model import ScheduledTask

def test_scheduled_task_due():
    """Test that ScheduledTask correctly reports when it is due."""
    task = ScheduledTask(name="demo", due_time=1234567890)
    assert task.is_due(1234567890)
```

## Behavior Guidelines

- AI should prefer adding small, focused functions over deeply nested logic.
- When uncertain between simplicity and abstraction, **choose readability**.

## Naming Conventions

- Use `snake_case` for functions, variables, and file names.
- Use `PascalCase` for class and dataclass names.
- Use `ALL_CAPS` for module-level constants.
- Prefix internal or private runtime fields with `_`.

## AI Prompt-Specific Behavior

- Avoid assumptions about the NVDA environment unless context explicitly requires it.
- Provide clean, minimal examples that work in a **non-NVDA Python interpreter**.
- Always add meaningful docstrings, especially for public APIs and dataclasses.
