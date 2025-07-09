
"""
Test utility dummies for PlanFlow Scheduler tests.

Provides DummySpeech and DummyCallback for use in pytest fixtures and assertions.
"""


class DummySpeech:
    """Dummy speech callback for capturing speech messages in tests."""
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def __call__(self, msg: str) -> None:
        """Capture a speech message."""
        self.messages.append(msg)




class DummyCallback:
    """Dummy callback for tracking invocation in tests.

    Attributes:
        called: True if callback was called at least once.
        calls: List of call timestamps (or call counts) for tracking multiple invocations.
    """
    def __init__(self) -> None:
        super().__init__()
        self.called: bool = False
        self.calls: list[float] = []

    def __call__(self) -> None:
        """Mark the callback as called and record the call timestamp."""
        self.called = True
        import time
        self.calls.append(time.time())
