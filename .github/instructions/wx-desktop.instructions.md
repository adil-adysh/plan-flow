---
applyTo: "desktop_ui/**"
---

# 🖥️ Desktop UI — UX & View Architecture Instructions

This document defines best practices and requirements for building a modular, testable, and maintainable wxPython-based desktop UI.

---

## 1. UI & UX Structure

- **Panel Composition:** Use `wx.Panel` with `wx.TAB_TRAVERSAL` to group interactive controls. Avoid applying `wx.TAB_TRAVERSAL` to individual controls.
- **Tab Order:** Respect sizer/control creation order. Use `MoveAfterInTabOrder()` only among sibling controls (same parent). Cross-panel tab order should follow logical layout via sizers.
- **Composite Widgets:** Use arrow keys for internal navigation in trees/lists/grids. Ensure no keyboard traps.
- **Focus Management:** Use `SetFocus()` when showing dialogs, overlays, or switching views. Restore focus to logical UI elements after dynamic transitions.
- **Read-Only Fields:** Prefer `SetEditable(False)` over `SetReadOnly(True)` when fields must stay reachable but not editable.

---

## 2. UI Regions & Functional Mapping

- **Planner Tree:**
  - Use `wx.TreeCtrl` with: `wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_HIDE_ROOT`
  - Support keyboard interaction: arrows, Enter, Home/End.
  - Trigger: `view_model.select_occurrence(node_id)`

- **Task Details Panel:**
  - Use `wx.StaticText` and `wx.TextCtrl(style=wx.TE_READONLY)` for label-value pairs.
  - Trigger: `view_model.get_selected_task_detail()`

- **Toolbar:**
  - Use `wx.Button` or `wx.BitmapButton` for actions like "Mark Done", "Refresh", "Today"
  - Bind actions using `wx.AcceleratorTable`
  - Trigger: `view_model.mark_selected_done()` and similar methods

- **Status Bar:**
  - Use `wx.StatusBar.SetStatusText(...)` for feedback messages

- **Logical Navigation Flow:**
```

Toolbar → Tree → Details → Toolbar (cyclic)

````

---

## 3. ViewModel Interface (Required)

All UI-triggered logic must route through the following interface:

```python
class DesktopViewModel:
  def refresh_tree(self) -> TreeNode: ...
  def select_occurrence(self, occ_id: str) -> None: ...
  def get_selected_task_detail(self) -> TaskDetailView: ...
  def mark_selected_done(self) -> None: ...
  def refresh(self) -> None: ...
  def get_today_summary(self) -> str: ...
````

---

## 4. Testing & Completion Criteria

* UI navigation works with Tab, arrow keys, and Enter/Space where applicable.
* All UI actions are routed via `DesktopViewModel`.
* No business logic (e.g., scheduling, file I/O, or network) is embedded in UI layer.
* Code passes linting and static typing (`ruff`, `pyright`).
* Unit tests (in `tests/desktop_ui/test_desktop_ui.py`) must cover:

  * Tree renders structure from ViewModel
  * Task selection updates detail panel
  * Toolbar actions invoke ViewModel
  * Today button focuses the correct date
  * Navigation follows intended focus flow

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

> Build modular, testable, and intuitive wxPython UIs. All UI logic must go through `DesktopViewModel`. Focus on structure, clarity, and separation of concerns.
