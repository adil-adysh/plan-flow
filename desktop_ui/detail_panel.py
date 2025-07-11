"""Task detail panel for PlanFlow desktop UI."""

import wx
from .view_model import DesktopViewModel, TaskDetailView
from datetime import datetime

class TaskDetailPanel(wx.Panel):
	"""Panel displaying details for the selected task occurrence."""
	def __init__(self, parent: wx.Window, view_model: DesktopViewModel) -> None:
		super().__init__(parent, style=wx.TAB_TRAVERSAL)
		self.view_model = view_model
		self.title = wx.StaticText(self, label="Title:")
		self.description = wx.TextCtrl(self, style=wx.TE_MULTILINE)
		self.description.SetName("Task Detail Edit")
		self.description.Enable(True)
		self.scheduled_for = wx.StaticText(self, label="Scheduled:")
		self.slot_name = wx.StaticText(self, label="Slot:")
		self.recurrence = wx.StaticText(self, label="Recurrence:")
		self.retries = wx.StaticText(self, label="Retries:")
		self.state = wx.StaticText(self, label="State:")
		self.SetName("Task Detail Panel")
		self._do_layout()
		# Tab order follows sizer/control creation order (panel with wx.TAB_TRAVERSAL)
		self.update_detail()

	def AcceptsFocusFromKeyboard(self) -> bool:
		return True

	def _do_layout(self) -> None:
		grid = wx.FlexGridSizer(0, 2, 5, 5)
		grid.AddMany([
			(self.title, 0, wx.ALIGN_RIGHT),
			(self.description, 1, wx.EXPAND),
			(self.scheduled_for, 0, wx.ALIGN_RIGHT),
			(self.slot_name, 0, wx.ALIGN_RIGHT),
			(self.recurrence, 0, wx.ALIGN_RIGHT),
			(self.retries, 0, wx.ALIGN_RIGHT),
			(self.state, 0, wx.ALIGN_RIGHT),
		])
		grid.AddGrowableCol(1, 1)
		self.SetSizer(grid)

	def update_detail(self) -> None:
		detail: TaskDetailView = self.view_model.get_selected_task_detail()
		self.title.SetLabel(f"Title: {detail.title}")
		self.description.SetValue(detail.description or "")
		self.scheduled_for.SetLabel(f"Scheduled: {detail.scheduled_for:%Y-%m-%d %H:%M}")
		self.slot_name.SetLabel(f"Slot: {detail.slot_name or '-'}")
		self.recurrence.SetLabel(f"Recurrence: {detail.recurrence}")
		self.retries.SetLabel(f"Retries: {detail.retries_remaining}")
		self.state.SetLabel(f"State: {detail.state}")
		# Color-code state
		color = wx.NullColour
		if detail.state == "done":
			color = wx.Colour(180, 180, 180)
		elif detail.state == "missed":
			color = wx.Colour(220, 0, 0)
		elif detail.state == "retrying":
			color = wx.Colour(255, 220, 0)
		self.state.SetForegroundColour(color)
		self.state.Refresh()
