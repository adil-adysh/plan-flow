import pytest
from typing import Any
from collections.abc import Callable
from types import SimpleNamespace
from tests.utils.dummies import DummySpeech

"""
Pytest fixtures for PlanFlow add-on tests.
Provides dummy callback, speech, and store objects for scheduler tests.
"""

class DummyCallback:
    """A dummy callback that records all invocations and arguments."""
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.called: bool = False

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append((args, kwargs))
        self.called = True


@pytest.fixture(scope="session")
def callback() -> DummyCallback:
    """
    Provides a reusable DummyCallback object scoped to the test session.
    Tracks call count and arguments for assertions.
    """
    return DummyCallback()


@pytest.fixture(autouse=True)
def reset_callback(callback: DummyCallback) -> None:
    """
    Reset the session-scoped callback state before each test for isolation.
    Ensures no state leakage between tests using autouse=True.
    """
    callback.called = False
    callback.calls.clear()


@pytest.fixture
def speech() -> DummySpeech:
    """
    Returns a dummy speech engine used to capture spoken messages in tests.
    """
    return DummySpeech()


class DummyStore:
    """
    An in-memory dummy task store that mimics basic task operations.
    Supports add, list, clear, and remove.
    Ensures task.callback is patched to match session-scoped DummyCallback.
    """
    def __init__(self, callback: DummyCallback) -> None:
        self.tasks: list[Any] = []
        self._callback = callback

    def add(self, task: Any) -> None:
        if hasattr(task, 'callback'):
            if getattr(task, 'callback', None) is None:
                task.callback = self._callback
        self.tasks.append(task)

    def list(self) -> list[Any]:
        return list(self.tasks)

    def clear(self) -> None:
        self.tasks.clear()

    def remove(self, task_id: Any) -> None:
        self.tasks = [t for t in self.tasks if getattr(t, 'id', None) != task_id]


@pytest.fixture
def store(callback: DummyCallback) -> DummyStore:
    """
    Returns a DummyStore instance that holds tasks and patches callback references.
    Uses the session-scoped callback fixture for consistent reference checks.
    """
    return DummyStore(callback)
