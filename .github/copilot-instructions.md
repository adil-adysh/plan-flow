
# Copilot Instructions for PlanFlow NVDA Add-on

## Project Overview

- **PlanFlow** is an NVDA add-on for natural language task scheduling, designed for accessibility and modularity.
- The codebase is structured for testability outside NVDA, with clear separation between NVDA-dependent and core logic.
- Core logic (task models, serialization, storage) is in `addon/globalPlugins/planflow/task/`.
- NVDA integration points (speech, hooks) should be isolated from core logic.

## Architecture & Patterns

- **Task Model:**  
  - `model.py`: Defines `ScheduledTask` (dataclass) with recurrence, callback, and due logic.
  - `serialiser.py`: Handles (de)serialization of tasks, including interval parsing.
  - `store.py`: `TaskStore` uses TinyDB for persistence, exposes add/update/remove/list/clear.
  - `schedule.py`: (Planned) Orchestrates scheduling, integrates with NVDA and TaskStore.
- **Relative Imports:**  
  - Always use relative imports within the package (e.g., `from .model import ScheduledTask`).
- **Fallback for `_()`:**  
  - If using `_()`, provide a fallback: `_ = lambda x: x` (see `buildVars.py`).
- **No print():**  
  - Use structured logging if needed; avoid `print()`.

## Build, Test, and Lint

- **Build:**  
  - Run `scons` in the project root to build the add-on (`.nvda-addon` file).
  - Run `scons pot` to generate translation template (`.pot`).
- **Test:**  
  - Unit tests are in `tests/` (e.g., `test_model.py` uses pytest).
  - Run tests with `pytest` (ensure testable code is NVDA-independent).
- **Lint/Format:**  
  - Use Ruff (`pyproject.toml` config) for linting and formatting.
  - Indentation: tabs (see `[tool.ruff.format]`).
  - Ignore W191 (tabs) for legacy files as needed.
- **Type Checking:**  
  - Use Pyright (`pyproject.toml` config) with `strict` mode.

## Developer Workflows

- **GitHub Actions:**  
  - `.github/workflows/build_addon.yml` automates build, lint, and packaging on PRs, pushes, and tags.
  - Artifacts and releases are handled automatically.
- **Localization:**  
  - Use `gettext` for translations.
  - Place `.po` files in `addon/locale/<lang>/LC_MESSAGES/`.
  - Manifest and docs are localized via templates and SCons.

## Conventions & Best Practices

- **Python 3.11.2+ required.**

**Type Hints:**
- Use Python 3.11+ type hint syntax throughout (e.g., `str | None` instead of `Optional[str]`).
- Do not use legacy `Optional[...]` or `Union[...]` syntax.
- **Docstrings:**  
  - All non-trivial functions/classes must have docstrings.
- **Composition over inheritance.**
- **No GUI unless explicitly requested.**
- **Avoid circular imports and module-level side effects.**
- **Manifest and build variables:**  
  - Edit `buildVars.py` for add-on metadata, not `sconstruct` or manifest files.
- **Documentation:**  
  - Place user docs in `addon/doc/<lang>/readme.md`.
  - Use `style.css` for HTML doc styling.

## Examples

- **Adding a new task field:**  
  - Update `ScheduledTask` in `model.py`, serialization in `serialiser.py`, and storage in `store.py`.
- **Testing a model change:**  
  - Add/modify tests in `tests/test_model.py`.

## Key Files & Directories

- `addon/globalPlugins/planflow/task/`: Core logic (model, store, serialization, scheduling)
- `buildVars.py`: Add-on metadata and build config
- `sconstruct`: Build script (SCons)
- `tests/`: Unit tests
- `.github/workflows/`: CI/CD automation

---

**Feedback requested:**  
Are there any unclear or missing sections? Let me know if you need more detail on architecture, workflows, or conventions.
