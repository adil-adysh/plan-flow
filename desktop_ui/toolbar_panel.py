"""Toolbar panel for PlanFlow desktop UI."""

import wx
from .view_model import DesktopViewModel

class PlannerToolBar(wx.Panel):
	"""Toolbar with actions: Mark Done, Refresh, Today."""
	def __init__(self, parent: wx.Window, view_model: DesktopViewModel) -> None:
		super().__init__(parent, style=wx.TAB_TRAVERSAL)
		self.view_model = view_model
		self.btn_done = wx.Button(self, label="Mark Done")
		self.btn_refresh = wx.Button(self, label="Refresh")
		self.btn_today = wx.Button(self, label="Today")
		self.btn_done.SetName("Mark Done Button")
		self.btn_refresh.SetName("Refresh Button")
		self.btn_today.SetName("Today Button")
		self.SetName("Planner Toolbar")
		self._do_layout()
		self.btn_done.Bind(wx.EVT_BUTTON, self.on_mark_done)
		self.btn_refresh.Bind(wx.EVT_BUTTON, self.on_refresh)
		self.btn_today.Bind(wx.EVT_BUTTON, self.on_today)

	def AcceptsFocusFromKeyboard(self) -> bool:
		return True

	def _do_layout(self) -> None:
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.btn_done, 0, wx.ALL, 5)
		hbox.Add(self.btn_refresh, 0, wx.ALL, 5)
		hbox.Add(self.btn_today, 0, wx.ALL, 5)
		self.SetSizer(hbox)

	def on_mark_done(self, event: wx.CommandEvent) -> None:
		self.view_model.mark_selected_done()
		self.GetParent().tree_panel._build_tree()
		self.GetParent().detail_panel.update_detail()

	def on_refresh(self, event: wx.CommandEvent) -> None:
		self.view_model.refresh()
		self.GetParent().tree_panel._build_tree()
		self.GetParent().detail_panel.update_detail()

	def on_today(self, event: wx.CommandEvent) -> None:
		# For demo: just refresh and select first node
		self.view_model.refresh()
		self.GetParent().tree_panel._build_tree()
		self.GetParent().detail_panel.update_detail()
