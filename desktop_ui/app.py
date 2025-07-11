"""Entry point for PlanFlow wxPython desktop UI."""


import wx
from desktop_ui.main_frame import MainFrame

class PlanFlowApp(wx.App):
	"""wx.App subclass for PlanFlow desktop UI."""
	def OnInit(self) -> bool:
		self.frame = MainFrame(None, title="PlanFlow Scheduler")
		self.frame.Show()
		return True

if __name__ == "__main__":
	app = PlanFlowApp()
	app.MainLoop()
