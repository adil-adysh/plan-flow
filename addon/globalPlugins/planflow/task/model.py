"""
Task model for PlanFlow: defines the ScheduledTask dataclass used for scheduling and recurrence logic.
This module is NVDA-independent and fully testable.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections.abc import Callable

@dataclass
class ScheduledTask:
	"""
	Represents a scheduled task with optional recurrence, description, and runtime callback.

	Fields:
	- id: Unique identifier for the task (UUID string).
	- label: Short label/title for the task.
	- time: When the task is due (datetime).
	- description: Optional detailed description.
	- link: Optional URL or reference.
	- recurrence: Optional recurrence interval (timedelta).
	- callback: (Runtime-only) Optional callable invoked when the task is due. Not persisted or serialized.
	"""
	id: str = field(default_factory=lambda: str(uuid.uuid4()))
	label: str = ""
	time: datetime = field(default_factory=datetime.now)
	description: str | None = None
	link: str | None = None
	recurrence: timedelta | None = None
	callback: Callable[[], None] | None = field(default=None, compare=False, repr=False)

	def is_due(self, ref: datetime | None = None) -> bool:
		"""
		Return True if the task is due at or before the given reference time.
		If ref is None, uses the current time.
		"""
		return (ref or datetime.now()) >= self.time
