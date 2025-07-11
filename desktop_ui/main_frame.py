"""Main window layout for PlanFlow desktop UI."""

import wx
from .toolbar_panel import PlannerToolBar
from .tree_panel import PlannerTreePanel
from .detail_panel import TaskDetailPanel
from .view_model import DesktopViewModel

class MainFrame(wx.Frame):
	"""Main window containing toolbar, tree, detail, and status bar."""
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.SetSize((900, 600))
		# Use a real backend-connected ViewModel
		self.view_model = DesktopViewModel()

		# Composite panel for all UI elements, with tab traversal
		self.composite_panel = wx.Panel(self, style=wx.TAB_TRAVERSAL)
		self.toolbar = PlannerToolBar(self.composite_panel, self.view_model)
		self.tree_panel = PlannerTreePanel(self.composite_panel, self.view_model)
		self.detail_panel = TaskDetailPanel(self.composite_panel, self.view_model)

		self.status_bar = self.CreateStatusBar()
		self.status_bar.SetStatusText(self.view_model.get_today_summary())

		self._do_layout()
		# Tab order: toolbar -> tree_panel -> detail_panel (handled by sizer order)
		self.Bind(wx.EVT_CLOSE, self.on_close)

	def _do_layout(self) -> None:
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar, 0, wx.EXPAND)
		vbox.Add(self.tree_panel, 1, wx.EXPAND)
		vbox.Add(self.detail_panel, 1, wx.EXPAND)
		self.composite_panel.SetSizer(vbox)
		frame_vbox = wx.BoxSizer(wx.VERTICAL)
		frame_vbox.Add(self.composite_panel, 1, wx.EXPAND)
		self.SetSizer(frame_vbox)

	def on_close(self, event: wx.CloseEvent) -> None:
		self.Destroy()
