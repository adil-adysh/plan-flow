

# Copilot Instructions for PlanFlow

## Project Structure & Key Concepts

- **Core logic** is in `addon/globalPlugins/planflow/task/`:
  - `task_model.py`: Data models (`TaskDefinition`, `TaskOccurrence`, etc.)
  - `calendar_planner.py`, `scheduler_service.py`, `recovery_service.py`, `execution_repository.py`: Scheduling, calendar, recovery, and storage logic
  - All modules are pure Python, fully typed, and testable outside NVDA
- **Tests** are in `tests/` (unit) and `tests/integration/` (integration)
- **Build config**: `buildVars.py` (metadata), `sconstruct` (SCons build script)
- **CI/CD**: `.github/workflows/` (automation)

## Coding Patterns & Conventions

- Use Python 3.11+ type hints (`str | None`, not `Optional[str]`)
- All classes/functions require Google-style docstrings
- Use `@dataclass(frozen=True, slots=True)` for models
- No NVDA APIs in core logic; NVDA-specific code is isolated elsewhere
- Use relative imports within packages
- No print statements; use logging if needed
- Indentation: tabs (see Ruff config)
- No GUI code unless explicitly requested

## Developer Workflows

- **Build:** Run `scons` in project root to build `.nvda-addon`
- **Test:** Run `pytest` for all tests (unit and integration)
- **Lint/Format:** Use Ruff (`pyproject.toml`)
- **Type Check:** Use Pyright in strict mode

## Examples

- To add a new model field: update in `task_model.py`, then update related logic and tests
- To test logic: add/modify tests in `tests/` using pytest fixtures and parameterization

## Reference Layout

- `addon/globalPlugins/planflow/task/`: Core modules
- `tests/`: Unit tests
- `tests/integration/`: Integration tests
- `buildVars.py`, `sconstruct`: Build config
- `.github/workflows/`: CI/CD

---

**Feedback requested:**
Is anything unclear or missing? Suggest improvements for architecture, workflows, or conventions.
