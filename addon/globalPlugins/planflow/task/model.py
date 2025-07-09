from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable
import uuid

@dataclass
class ScheduledTask:
    """
    Represents a scheduled task with optional recurrence and description.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    time: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
    link: Optional[str] = None
    recurrence: Optional[timedelta] = None

    # Runtime-only: a callable to be invoked when task is due
    callback: Optional[Callable[[], None]] = field(default=None, compare=False, repr=False)

    def is_due(self, ref: Optional[datetime] = None) -> bool:
        """
        Determines if the task is due relative to a reference time (default: now).
        """
        return (ref or datetime.now()) >= self.time
