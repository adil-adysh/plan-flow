
"""
Test utility dummies for PlanFlow Scheduler tests.

Provides DummySpeech and DummyCallback for use in pytest fixtures and assertions.
"""


class DummySpeech:
    """Dummy speech callback for capturing speech messages in tests."""
    def __init__(self) -> None:
        self.messages: list[str] = []

    def __call__(self, msg: str) -> None:
        """Capture a speech message."""
        self.messages.append(msg)



class DummyCallback:
    """Dummy callback for tracking invocation in tests."""
    def __init__(self) -> None:
        self.called: bool = False

    def __call__(self) -> None:
        """Mark the callback as called."""
        self.called = True
