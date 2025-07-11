"""SmartSchedulerController: High-level coordination and delegation for smart scheduling.

Provides a simplified, testable interface for controlling task scheduling, retry, recovery, and timer state.
"""

from typing import Callable
from datetime import datetime
from .smart_scheduler_service import SmartSchedulerService
from .execution_repository import ExecutionRepository
from .scheduler_service import TaskScheduler
from .recovery_service import RecoveryService
from .calendar_planner import CalendarPlanner
from .task_model import TaskOccurrence, TaskDefinition

class SmartSchedulerController:
	"""High-level controller for smart scheduling, retry, and recovery.

	Bridges UI/event layers and SmartSchedulerService, providing declarative control and validation.
	"""
	def __init__(
		self,
		smart_scheduler: SmartSchedulerService,
		repo: ExecutionRepository,
		scheduler: TaskScheduler,
		recovery: RecoveryService,
		calendar: CalendarPlanner,
		now_fn: Callable[[], datetime] = datetime.now
	) -> None:
		"""Initialize SmartSchedulerController with dependencies.

		Args:
			smart_scheduler: The smart scheduler service instance.
			repo: Execution repository for tasks and occurrences.
			scheduler: Task scheduler for retry/recurrence logic.
			recovery: Recovery service for missed tasks.
			calendar: Calendar planner for slot validation.
			now_fn: Callable returning current datetime (for testability).
		"""
		self._smart_scheduler = smart_scheduler
		self._repo = repo
		self._scheduler = scheduler
		self._recovery = recovery
		self._calendar = calendar
		self._now_fn = now_fn

	def start(self) -> None:
		"""Start the scheduler, schedule all valid future tasks, and check for missed ones.

		Raises:
			None
		"""
		self._smart_scheduler.start()

	def pause(self) -> None:
		"""Pause all scheduling and timers.

		Raises:
			None
		"""
		self._smart_scheduler.pause()

	def resume(self) -> None:
		"""Resume paused state and schedule all valid tasks.

		Raises:
			None
		"""
		self._smart_scheduler.start()

	def mark_done(self, occ_id: str) -> None:
		"""Mark a TaskOccurrence as done, and schedule retry or recurrence.

		Args:
			occ_id: The ID of the occurrence to mark as done.

		Raises:
			ValueError: If the occurrence does not exist.
		"""
		occ = self._get_occurrence(occ_id)
		if self._already_done(occ_id):
			raise ValueError(f"Occurrence {occ_id} is already marked done.")
		# Mark as done in repo
		self._repo.add_execution_for_occurrence(occ)
		# Try retry
		retry_occ = self._scheduler.reschedule_retry(occ, self._now_fn())
		if retry_occ:
			self._smart_scheduler.schedule_occurrence(retry_occ)
			return
		# Try recurrence
		task = self._get_task(occ.task_id)
		if getattr(task, "recurrence", None):
			next_occ = self._scheduler.get_next_occurrence(task, self._now_fn())
			if next_occ:
				self._smart_scheduler.schedule_occurrence(next_occ)

	def retry_occurrence(self, occ_id: str) -> TaskOccurrence | None:
		"""Manually trigger retry if allowed by policy.

		Args:
			occ_id: The ID of the occurrence to retry.

		Returns:
			The new TaskOccurrence if retry is allowed, else None.

		Raises:
			ValueError: If the occurrence does not exist.
		"""
		occ = self._get_occurrence(occ_id)
		if self._already_done(occ_id):
			return None
		retry_occ = self._scheduler.reschedule_retry(occ, self._now_fn())
		if retry_occ:
			self._smart_scheduler.schedule_occurrence(retry_occ)
			return retry_occ
		return None

	def get_scheduled_occurrences(self) -> list[TaskOccurrence]:
		"""Return currently scheduled TaskOccurrences.

		Returns:
			A list of currently scheduled TaskOccurrence objects.
		"""
		return self._smart_scheduler.get_scheduled_occurrences()

	def recover_missed_tasks(self) -> list[TaskOccurrence]:
		"""Run recovery for all missed and eligible tasks.

		Returns:
			A list of new TaskOccurrence objects created by recovery.
		"""
		all_executions = self._repo.list_executions()
		all_occurrences = {o.id: o for o in self._repo.list_occurrences()}
		all_tasks = {t.id: t for t in self._repo.list_tasks()}
		new_occs = self._recovery.recover_missed_occurrences(
			executions=all_executions,
			occurrences=all_occurrences,
			tasks=all_tasks,
			now=self._now_fn(),
			calendar=self._calendar,
			scheduled_occurrences=list(all_occurrences.values()),
			working_hours=self._calendar.working_hours,
			slot_pool=self._calendar.slot_pool,
			max_per_day=self._calendar.max_per_day
		)
		for occ in new_occs:
			self._smart_scheduler.schedule_occurrence(occ)
		return new_occs

	def _get_occurrence(self, occ_id: str) -> TaskOccurrence:
		"""Fetch a TaskOccurrence by ID, or raise ValueError if not found."""
		for occ in self._repo.list_occurrences():
			if occ.id == occ_id:
				return occ
		raise ValueError(f"Occurrence {occ_id} not found.")

	def _get_task(self, task_id: str) -> TaskDefinition:
		"""Fetch a TaskDefinition by ID, or raise ValueError if not found."""
		for task in self._repo.list_tasks():
			if task.id == task_id:
				return task
		raise ValueError(f"Task {task_id} not found.")

	def _already_done(self, occ_id: str) -> bool:
		"""Return True if the occurrence is already marked done."""
		return any(e.occurrence_id == occ_id and e.state == "done" for e in self._repo.list_executions())
