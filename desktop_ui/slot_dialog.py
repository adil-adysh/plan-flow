"""Dialog for adding or editing a Slot (TimeSlot) in PlanFlow."""

import wx
from datetime import time

class SlotDialog(wx.Dialog):
	"""Dialog for creating or editing a slot (TimeSlot)."""
	def __init__(self, parent: wx.Window, title: str = "Add Slot", slot_name: str = "", start: time | None = None, end: time | None = None) -> None:
		super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.SetSize((350, 220))

		self.name_label = wx.StaticText(self, label="Slot Name:")
		self.name_ctrl = wx.TextCtrl(self, value=slot_name)
		self.start_label = wx.StaticText(self, label="Start Time (HH:MM):")
		self.start_ctrl = wx.TextCtrl(self, value=start.strftime("%H:%M") if start else "")
		self.end_label = wx.StaticText(self, label="End Time (HH:MM):")
		self.end_ctrl = wx.TextCtrl(self, value=end.strftime("%H:%M") if end else "")

		self.btn_ok = wx.Button(self, wx.ID_OK, "Save")
		self.btn_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")

		self._do_layout()
		self.Bind(wx.EVT_BUTTON, self.on_ok, self.btn_ok)
		self.name_ctrl.SetFocus()

	def _do_layout(self) -> None:
		grid = wx.FlexGridSizer(0, 2, 10, 10)
		grid.AddMany([
			(self.name_label, 0, wx.ALIGN_RIGHT), (self.name_ctrl, 1, wx.EXPAND),
			(self.start_label, 0, wx.ALIGN_RIGHT), (self.start_ctrl, 1, wx.EXPAND),
			(self.end_label, 0, wx.ALIGN_RIGHT), (self.end_ctrl, 1, wx.EXPAND),
		])
		grid.AddGrowableCol(1, 1)
		btn_sizer = wx.StdDialogButtonSizer()
		btn_sizer.AddButton(self.btn_ok)
		btn_sizer.AddButton(self.btn_cancel)
		btn_sizer.Realize()
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(grid, 1, wx.ALL | wx.EXPAND, 15)
		vbox.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
		self.SetSizer(vbox)

	def on_ok(self, event: wx.CommandEvent) -> None:
		if not self.name_ctrl.GetValue().strip():
			wx.MessageBox("Slot name is required.", "Error", wx.ICON_ERROR)
			return
		if not self._parse_time(self.start_ctrl.GetValue()):
			wx.MessageBox("Start time must be in HH:MM format.", "Error", wx.ICON_ERROR)
			return
		if not self._parse_time(self.end_ctrl.GetValue()):
			wx.MessageBox("End time must be in HH:MM format.", "Error", wx.ICON_ERROR)
			return
		self.EndModal(wx.ID_OK)

	def get_slot_data(self) -> tuple[str, time, time]:
		"""Return the slot name, start, and end time."""
		return (
			self.name_ctrl.GetValue().strip(),
			self._parse_time(self.start_ctrl.GetValue()),
			self._parse_time(self.end_ctrl.GetValue()),
		)

	@staticmethod
	def _parse_time(value: str) -> time | None:
		try:
			h, m = map(int, value.strip().split(":"))
			return time(hour=h, minute=m)
		except Exception:
			return None
