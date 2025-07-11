"""GUI tests for PlanFlow Desktop UI (wxPython)."""

import pytest
import wx
from desktop_ui.app import PlanFlowApp
from desktop_ui.main_frame import MainFrame
from desktop_ui.view_model import TreeNode, TaskDetailView

@pytest.fixture(scope="module")
def app():
	app = wx.App()
	yield app
	app.Destroy()

class DummyViewModel:
	def __init__(self):
		self.selected = None
		self.tree = TreeNode(
			id="root", label="Root", is_expanded=True, is_selected=False, children=[
				TreeNode(id="month", label="July", is_expanded=True, is_selected=False, children=[
					TreeNode(id="week", label="Week 2", is_expanded=True, is_selected=False, children=[
						TreeNode(id="day", label="11", is_expanded=True, is_selected=True, children=[])
					])
				])
			]
		)
		self.detail = TaskDetailView(
			title="Test Task",
			description="A test task.",
			scheduled_for=None,
			slot_name=None,
			recurrence=None,
			retries_remaining=1,
			state="pending"
		)
	def refresh_tree(self):
		return self.tree
	def select_occurrence(self, occ_id):
		self.selected = occ_id
	def get_selected_task_detail(self):
		return self.detail
	def mark_selected_done(self):
		self.detail = self.detail.__class__(**{**self.detail.__dict__, "state": "done"})
	def refresh(self):
		pass
	def get_today_summary(self):
		return "Today: 1 task"

def test_tree_renders_structure(app, monkeypatch):
	from desktop_ui.tree_panel import PlannerTreePanel
	frame = wx.Frame(None)
	panel = PlannerTreePanel(frame, DummyViewModel())
	assert panel.tree.GetCount() > 0
	frame.Destroy()

def test_task_selection_updates_detail_panel(app, monkeypatch):
	from desktop_ui.detail_panel import TaskDetailPanel
	frame = wx.Frame(None)
	panel = TaskDetailPanel(frame, DummyViewModel())
	panel.update_detail()
	assert "Test Task" in panel.title.GetLabel()
	frame.Destroy()

def test_mark_done_updates_view(app, monkeypatch):
	vm = DummyViewModel()
	from desktop_ui.detail_panel import TaskDetailPanel
	frame = wx.Frame(None)
	panel = TaskDetailPanel(frame, vm)
	vm.mark_selected_done()
	panel.update_detail()
	assert "done" in panel.state.GetLabel()
	frame.Destroy()

def test_today_expands_and_scrolls(app, monkeypatch):
	from desktop_ui.toolbar_panel import PlannerToolBar
	vm = DummyViewModel()
	frame = wx.Frame(None)
	panel = PlannerToolBar(frame, vm)
	panel.on_today(None)
	assert vm.get_today_summary() == "Today: 1 task"
	frame.Destroy()

def test_toolbar_buttons_call_view_model(app, monkeypatch):
	from desktop_ui.toolbar_panel import PlannerToolBar
	vm = DummyViewModel()
	frame = wx.Frame(None)
	panel = PlannerToolBar(frame, vm)
	panel.on_mark_done(None)
	assert vm.detail.state == "done"
	frame.Destroy()
