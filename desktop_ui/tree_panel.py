import wx
from .view_model import DesktopViewModel, TreeNode

class AccessibleTreeCtrl(wx.TreeCtrl):
	"""A TreeCtrl that allows Tab/Shift+Tab to move focus out for accessibility."""
	def __init__(self, parent: wx.Window, style: int = 0) -> None:
		super().__init__(parent, style=style)
		self.Bind(wx.EVT_CHAR, self.on_char)

	def on_char(self, event: wx.KeyEvent) -> None:
		key = event.GetKeyCode()
		if key == wx.WXK_TAB:
			nav_event = wx.NavigationKeyEvent()
			nav_event.SetDirection(not event.ShiftDown())
			nav_event.SetCurrentFocus(self)
			wx.PostEvent(self.GetParent(), nav_event)
		else:
			event.Skip()

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
		self.tree.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
		self._do_layout()

	def on_context_menu(self, event: wx.ContextMenuEvent) -> None:
		pos = event.GetPosition()
		if pos == wx.DefaultPosition:
			item = self.tree.GetSelection()
			if not item or not item.IsOk():
				return
		else:
			pos = self.tree.ScreenToClient(pos)
			item, _ = self.tree.HitTest(pos)
			if not item or not item.IsOk():
				return
		label = self.tree.GetItemText(item)
		menu = wx.Menu()
		if label.isdigit():
			add_slot_item = menu.Append(wx.ID_ANY, "Add Slot")
			self.Bind(wx.EVT_MENU, lambda evt, i=item: self.on_add_slot(i), add_slot_item)
		elif '(' in label and ')' in label:
			add_task_item = menu.Append(wx.ID_ANY, "Add Task")
			self.Bind(wx.EVT_MENU, lambda evt, i=item: self.on_add_task(i), add_task_item)
		if menu.GetMenuItemCount() > 0:
			self.PopupMenu(menu)
		menu.Destroy()

	def on_add_task(self, item):
		label = self.tree.GetItemText(item)
		parent_item = self.tree.GetItemParent(item)
		day_label = self.tree.GetItemText(parent_item)
		slot_name = label.split('(')[0].strip()
		dlg = wx.TextEntryDialog(self, f"Enter task title for slot '{slot_name}':", "Add Task")
		if dlg.ShowModal() == wx.ID_OK:
			title = dlg.GetValue().strip()
			if title:
				if hasattr(self.view_model, "add_task_to_slot"):
					self.view_model.add_task_to_slot(day_label, slot_name, title)
					self._build_tree()
		dlg.Destroy()

	def on_add_slot(self, item: wx.TreeItemId) -> None:
		from .slot_dialog import SlotDialog
		dialog = SlotDialog(self, title="Add Slot")
		if dialog.ShowModal() == wx.ID_OK:
			name, start, end = dialog.get_slot_data()
			if hasattr(self.view_model, "add_slot"):
				# Use the full node ID (day_id) for slot storage
				def get_full_day_id(node: wx.TreeItemId) -> str:
					labels: list[str] = []
					root = self.tree.GetRootItem()
					while node and node.IsOk() and node != root:
						labels.append(self.tree.GetItemText(node))
						node = self.tree.GetItemParent(node)
					labels = [label for label in labels if label]  # Remove empty root
					return ':'.join(reversed(labels))
				day_id = get_full_day_id(item)
				before = set(tuple(s.items()) for s in getattr(self.view_model, '_slots_by_day', {}).get(day_id, []))
				self.view_model.add_slot(day_id, name, start, end)
				after = set(tuple(s.items()) for s in getattr(self.view_model, '_slots_by_day', {}).get(day_id, []))
				if len(after) > len(before):
					self._build_tree()
		dialog.Destroy()
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
			self.view_model.select_occurrence(label)
			frame = wx.GetTopLevelParent(self)
			if hasattr(frame, "detail_panel"):
				frame.detail_panel.update_detail()
