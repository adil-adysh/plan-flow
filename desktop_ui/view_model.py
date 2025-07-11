"""Adapter between controller and UI for PlanFlow desktop UI."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

@dataclass(frozen=True, slots=True)
class TreeNode:
	id: str
	label: str
	children: list['TreeNode']
	is_expanded: bool
	is_selected: bool

@dataclass(frozen=True, slots=True)
class TaskDetailView:
	title: str
	description: str | None
	scheduled_for: datetime
	slot_name: str | None
	recurrence: timedelta | None
	retries_remaining: int
	state: Literal["pending", "done", "missed", "retrying"]


from addon.globalPlugins.planflow.task.execution_repository import ExecutionRepository
from addon.globalPlugins.planflow.task.smart_scheduler_controller import SmartSchedulerController
from addon.globalPlugins.planflow.task.smart_scheduler_service import SmartSchedulerService
from addon.globalPlugins.planflow.task.scheduler_service import TaskScheduler
from addon.globalPlugins.planflow.task.calendar_planner import CalendarPlanner
from addon.globalPlugins.planflow.task.recovery_service import RecoveryService
from addon.globalPlugins.planflow.task.task_model import TaskOccurrence, TaskExecution, TaskDefinition
from datetime import datetime
from typing import Any

class DesktopViewModel:
	"""Adapter between controller and UI for PlanFlow desktop UI."""

	def __init__(self) -> None:
		self.repo = ExecutionRepository()
		self.calendar = CalendarPlanner()
		self.scheduler = TaskScheduler()
		self.recovery = RecoveryService()
		self.smart_service = SmartSchedulerService(
			execution_repo=self.repo,
			scheduler=self.scheduler,
			calendar=self.calendar,
			recovery=self.recovery,
			now_fn=datetime.now
		)
		self.controller = SmartSchedulerController(
			smart_scheduler=self.smart_service,
			repo=self.repo,
			scheduler=self.scheduler,
			recovery=self.recovery,
			calendar=self.calendar,
			now_fn=datetime.now
		)
		self.selected_occ_id: str | None = None

		# --- DEMO DATA ---
		from addon.globalPlugins.planflow.task.task_model import TaskDefinition, TaskOccurrence, RetryPolicy
		from datetime import timedelta
		import random
		# Add a demo task
		task = TaskDefinition(
			id="demo-task-1",
			title="Demo Task",
			description="This is a demo task.",
			link=None,
			created_at=datetime.now(),
			recurrence=timedelta(days=1),
			priority="medium",
			preferred_slots=[],
			retry_policy=RetryPolicy(max_retries=2),
			pinned_time=None
		)
		self.repo.add_task(task)
		# Add a few demo occurrences
		for i in range(3):
			occ = TaskOccurrence(
				id=f"demo-occ-{i+1}",
				task_id=task.id,
				scheduled_for=datetime.now() + timedelta(days=i),
				slot_name=None,
				pinned_time=None
			)
			self.repo.add_occurrence(occ)
		# Optionally, select the first occurrence by default
		self.selected_occ_id = "demo-occ-1"

	def refresh_tree(self) -> TreeNode:
		"""Return the root TreeNode for the planner tree."""
		# Group by month/week/day/task for demo
		occs = self.repo.list_occurrences()
		occs_by_date: dict[str, list[TaskOccurrence]] = {}
		for occ in occs:
			key = occ.scheduled_for.strftime("%Y-%m-%d")
			occs_by_date.setdefault(key, []).append(occ)
		months: dict[str, dict[str, list[TaskOccurrence]]] = {}
		for date_str, occs_on_day in occs_by_date.items():
			dt = datetime.strptime(date_str, "%Y-%m-%d")
			month = dt.strftime("%B %Y")
			week = f"Week {dt.isocalendar().week}"
			months.setdefault(month, {}).setdefault(week, []).extend(occs_on_day)
		root = TreeNode(id="root", label="Planner", children=[], is_expanded=True, is_selected=False)
		for month, weeks in months.items():
			month_node = TreeNode(id=month, label=month, children=[], is_expanded=True, is_selected=False)
			for week, days in weeks.items():
				week_node = TreeNode(id=f"{month}:{week}", label=week, children=[], is_expanded=True, is_selected=False)
				# Group by day
				by_day: dict[str, list[TaskOccurrence]] = {}
				for occ in days:
					day = occ.scheduled_for.strftime("%d")
					by_day.setdefault(day, []).append(occ)
					# ...
				for day, occs_in_day in by_day.items():
					day_node = TreeNode(id=f"{month}:{week}:{day}", label=day, children=[], is_expanded=True, is_selected=False)
					for occ in occs_in_day:
						is_selected = occ.id == self.selected_occ_id
						task = self.repo.get_task(occ.task_id)
						label = task.title if task else occ.id
						occ_node = TreeNode(id=occ.id, label=label, children=[], is_expanded=False, is_selected=is_selected)
						day_node.children.append(occ_node)
					week_node.children.append(day_node)
				month_node.children.append(week_node)
			root.children.append(month_node)
		return root

	def select_occurrence(self, occ_id: str) -> None:
		"""Select a task occurrence by ID."""
		self.selected_occ_id = occ_id

	def get_selected_task_detail(self) -> TaskDetailView:
		"""Return details for the currently selected task occurrence."""
		if not self.selected_occ_id:
			return TaskDetailView(
				title="No Task Selected",
				description=None,
				scheduled_for=datetime.now(),
				slot_name=None,
				recurrence=None,
				retries_remaining=0,
				state="pending"
			)
		occ = next((o for o in self.repo.list_occurrences() if o.id == self.selected_occ_id), None)
		if not occ:
			return TaskDetailView(
				title="Not Found",
				description=None,
				scheduled_for=datetime.now(),
				slot_name=None,
				recurrence=None,
				retries_remaining=0,
				state="pending"
			)
		task = self.repo.get_task(occ.task_id)
		exec = next((e for e in self.repo.list_executions() if e.occurrence_id == occ.id), None)
		return TaskDetailView(
			title=task.title if task else occ.id,
			description=task.description if task else None,
			scheduled_for=occ.scheduled_for,
			slot_name=occ.slot_name,
			recurrence=task.recurrence if task else None,
			retries_remaining=exec.retries_remaining if exec else 0,
			state=exec.state if exec else "pending"
		)

	def mark_selected_done(self) -> None:
		"""Mark the selected occurrence as done."""
		if self.selected_occ_id:
			self.controller.mark_done(self.selected_occ_id)

	def refresh(self) -> None:
		"""Refresh all planner data."""
		self.smart_service.schedule_all()

	def get_today_summary(self) -> str:
		"""Return a summary string for today."""
		today = datetime.now().date()
		tasks_today = [o for o in self.repo.list_occurrences() if o.scheduled_for.date() == today]
		return f"Today: {len(tasks_today)} task(s)"
