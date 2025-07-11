# ...existing code...
import wx
from .view_model import DesktopViewModel, TreeNode

class AccessibleTreeCtrl(wx.TreeCtrl):
	"""A TreeCtrl that allows Tab/Shift+Tab to move focus out for accessibility.

	This subclass overrides EVT_CHAR to intercept Tab/Shift+Tab and calls Navigate
	so keyboard users can move focus out of the tree control.
	"""
	def __init__(self, parent: 'wx.Window', style: int = 0) -> None:
		"""Initialize the accessible tree control.

		Args:
			parent: The parent wx.Window.
			style: wx.TreeCtrl style flags.

		Returns:
			None
		"""
		super().__init__(parent, style=style)
		self.Bind(wx.EVT_CHAR, self.on_char)

	def on_char(self, event: 'wx.KeyEvent') -> None:
		"""Handle key events to allow Tab/Shift+Tab traversal out of the tree.

		Args:
			event: The wx.KeyEvent instance.

		Returns:
			None
		"""
		key: int = event.GetKeyCode()
		if key == wx.WXK_TAB:
			nav_event = wx.NavigationKeyEvent()
			nav_event.SetDirection(not event.ShiftDown())
			nav_event.SetCurrentFocus(self)
			# Send navigation event to the parent panel so focus moves out of the tree
			wx.PostEvent(self.GetParent(), nav_event)
		else:
			event.Skip()
# ...existing code...

class PlannerTreePanel(wx.Panel):
	"""Panel displaying the planner tree structure."""
	def __init__(self, parent: wx.Window, view_model: DesktopViewModel) -> None:
		super().__init__(parent, style=wx.TAB_TRAVERSAL)
		self.view_model = view_model
		self.tree = AccessibleTreeCtrl(
			self,
			style=wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_HIDE_ROOT | wx.WANTS_CHARS
		)
		self.tree.SetName("Planner Tree")
		self.tree.Enable(True)
		self._build_tree()
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_selection)
		self._do_layout()
		# Ensure panel is focusable for Tab traversal
		self.SetWindowStyleFlag(wx.TAB_TRAVERSAL)


	def AcceptsFocusFromKeyboard(self) -> bool:
		return True

	def _do_layout(self) -> None:
		box = wx.BoxSizer(wx.VERTICAL)
		box.Add(self.tree, 1, wx.EXPAND)
		self.SetSizer(box)

	def _build_tree(self) -> None:
		root_node = self.view_model.refresh_tree()
		self.tree.DeleteAllItems()
		root = self.tree.AddRoot("")
		self._add_nodes(root, root_node)

	def _add_nodes(self, parent_item, node: TreeNode) -> None:
		for child in node.children:
			item = self.tree.AppendItem(parent_item, child.label)
			if child.is_expanded:
				self.tree.Expand(item)
			if child.is_selected:
				self.tree.SelectItem(item)
			self._add_nodes(item, child)

	def on_selection(self, event: wx.TreeEvent) -> None:
		item = event.GetItem()
		if item:
			label = self.tree.GetItemText(item)
			# Find node by label (for demo; real code should use IDs)
			self.view_model.select_occurrence(label)
			frame = wx.GetTopLevelParent(self)
			if hasattr(frame, "detail_panel"):
				frame.detail_panel.update_detail()
