---
applyTo: "desktop_ui/**"
---

# 🖥️ PlanFlow Desktop UI — Accessibility & UX Instructions

This document defines best practices and requirements for building a robust, accessible, and testable wxPython-based GUI for PlanFlow.

---

## 1. Accessibility & Keyboard Navigation (NVDA/wxPython)

- **Panel Structure:** Always group interactive controls inside a `wx.Panel` with `wx.TAB_TRAVERSAL` style. Never apply `wx.TAB_TRAVERSAL` to individual controls.
- **Tab Order:** Tab order follows sizer/control creation order. Use `MoveAfterInTabOrder` only for sibling controls (same parent). For cross-panel tab order, rely on sizer order.
- **Composite Widgets:** Trees, lists, and grids should be a single tab stop; use arrow keys for internal navigation. Avoid keyboard traps.
- **Focus Management:** Use `Enable(True)` to ensure controls are focusable. Do not use `SetFocusable` (not supported). For dynamic UIs, set focus with `SetFocus()` when new dialogs or overlays appear, and restore focus when they close. If NVDA skips the first focusable element, set focus programmatically after window creation.
- **Read-Only Fields:** Use `SetEditable(False)` (not `SetReadOnly(True)`) for text fields that should remain in the tab order but not accept input. If you need screen readers to announce "read-only," implement a custom `wx.Accessible` and set `STATE_SYSTEM_READONLY`.
- **Custom Controls:** For custom widgets, subclass `wx.Accessible` and override `GetName`, `GetRole`, `GetValue`, `GetState`, and `NotifyEvent` to expose correct semantics and state changes. Attach your custom accessible object with `SetAccessible()`.
- **Dynamic Content:** When UI content changes, call `NotifyEvent()` on the accessible object (e.g., `EVENT_OBJECT_VALUECHANGE`, `EVENT_OBJECT_STATECHANGE`). Move focus to new content or status messages as appropriate, and restore focus when overlays close.
- **Naming & Roles:** Always set accessible names with `SetName()` or `SetLabel()` for all interactive controls. Ensure all controls expose correct roles, names, values, and states (see MSAA: Role, Name, Value, State).
- **Edge Cases:** Never use `SetReadOnly(True)` if you want a text field to remain in the tab order—use `SetEditable(False)` instead. Never use `MoveAfterInTabOrder` or `MoveBeforeInTabOrder` between controls with different parents. Never apply `wx.TAB_TRAVERSAL` to non-container widgets. For `wx.grid.Grid`, do not rely on default cell implementation for accessibility—use focusable controls or custom accessible roles.
- **Troubleshooting:** Use NVDA's "Highlight focus" feature to debug focus issues. Consult NVDA/wxPython forums, GitHub, and mailing lists for platform-specific accessibility bugs and workarounds.

---

## 2. UX & UI Structure

- **Planner Tree:** Use `wx.TreeCtrl` with `wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_HIDE_ROOT`. Enable keyboard navigation (arrows, Enter, Home/End). Call `view_model.select_occurrence(node_id)` on selection. Use `SetName("Planner Tree")`.
- **Task Details:** Use `wx.StaticText` and `wx.TextCtrl(style=wx.TE_READONLY)` for fields. Call `view_model.get_selected_task_detail()`. Use `SetLabel()` and `SetName()` for all fields.
- **Toolbar:** Use `wx.Button` or `wx.BitmapButton` for actions ("Mark Done", "Refresh", "Today"). Attach keyboard shortcuts with `wx.AcceleratorTable`. Use `SetName()` or `SetLabel()` for accessibility. Call `view_model.mark_selected_done()`, etc.
- **Status Bar:** Use `wx.StatusBar.SetStatusText(...)` for feedback.
- **Logical Focus Order:** Toolbar → Tree → Details → Toolbar (cyclic).

---

## 3. ViewModel Interface (Required)

All UI actions must route through this interface:

```python
class DesktopViewModel:
    def refresh_tree(self) -> TreeNode: ...
    def select_occurrence(self, occ_id: str) -> None: ...
    def get_selected_task_detail(self) -> TaskDetailView: ...
    def mark_selected_done(self) -> None: ...
    def refresh(self) -> None: ...
    def get_today_summary(self) -> str: ...
```

---

## 4. Testing & Completion Criteria

- All panels and controls are keyboard-navigable (Tab, arrows, Enter/Space).
- All interactive elements have accessible names and roles.
- All UI actions are routed through the ViewModel.
- No `print()` or scheduler logic in the UI layer.
- Lint and type check clean (ruff + pyright).
- Tests in `tests/desktop_ui/test_desktop_ui.py` cover:
    - Tree renders structure from ViewModel
    - Task selection updates details
    - Toolbar actions call ViewModel
    - Today button focuses current day
    - Keyboard tab traversal order
    - Screen reader labels present

---

## 5. Directory Layout

```
desktop_ui/
├── app.py
├── main_frame.py
├── tree_panel.py
├── detail_panel.py
├── toolbar_panel.py
├── view_model.py
├── assets/
│   └── icons/
tests/
└── desktop_ui/
    └── test_desktop_ui.py
```

---

> This UI must be screen-reader-friendly, keyboard-accessible, and modular. Every action routes through the `DesktopViewModel`. Follow these rules for robust, inclusive, and maintainable wxPython desktop UI.
All UI actions must route through this interface.
