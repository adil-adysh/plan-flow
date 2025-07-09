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
