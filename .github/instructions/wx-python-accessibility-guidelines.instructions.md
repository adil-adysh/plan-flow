---
applyTo: "**"
---

## ✅ General Principles

- Ensure keyboard navigability using correct container structures.
- Use semantic roles via `wx.Accessible` where needed.
- Explicitly notify assistive tech of dynamic UI changes.
- Maintain predictable and visible keyboard focus.

---

## 🧭 Tab Navigation and Focus Management

- Always wrap interactive controls in a `wx.Panel` with `wx.TAB_TRAVERSAL`.
- **Do not** apply `wx.TAB_TRAVERSAL` directly to widgets like `wx.TextCtrl`.

```python
panel = wx.Panel(parent, style=wx.TAB_TRAVERSAL)
````

* Use `SetFocus()` to direct focus to logical elements during state changes (e.g., dialogs opening/closing).

```python
dialog.Show()
dialog.inputField.SetFocus()
```

---

## 🧩 Read-only Text Controls

* Prefer `SetEditable(False)` instead of `SetReadOnly(True)` to retain focusability.

```python
ctrl = wx.TextCtrl(parent)
ctrl.SetEditable(False)  # Keeps control in tab order
```

* If needed, use `wx.Accessible` to expose `STATE_SYSTEM_READONLY`.

```python
class ReadOnlyAccessible(wx.Accessible):
    def GetState(self, childId):
        return wx.STATE_SYSTEM_READONLY
```

---

## 📣 Dynamic UI Changes

* Always call `NotifyEvent()` when the UI updates dynamically.

```python
self.NotifyEvent(wx.wxEVT_ACCESSIBILITY_VALUE_CHANGE, self, wx.OBJID_CLIENT, 0)
```

* Maintain focus continuity — move focus to a newly visible element or restore to a meaningful prior control.

---

## 📊 Custom Controls and wx.grid.Grid

* Avoid non-focusable elements like `wx.StaticText` inside interactive widgets.
* Use `wx.TextCtrl` in grid cells for keyboard and screen reader access.

```python
grid.SetCellEditor(row, col, wx.grid.GridCellTextEditor())
```

* Alternatively, subclass `wx.Accessible` to set roles like `ROLE_SYSTEM_TABLE`, `ROLE_SYSTEM_CELL`.

```python
class MyGridAccessible(wx.Accessible):
    def GetRole(self, childId):
        return wx.ROLE_SYSTEM_CELL
```

---

## 🔄 Composite Widgets and Roving Focus

* Use arrow-key-based navigation inside grouped controls while keeping a single tab stop.
* Use techniques similar to `aria-activedescendant` (conceptually) by tracking "active" subcomponents.

---

## 🛠 Accessible Class Implementation

Use the following key methods from `wx.Accessible`:

* `GetName(self, childId, name)`
* `GetRole(self, childId, role)`
* `GetState(self, childId, state)`
* `NotifyEvent(self, eventType, window, objectType, objectId)`

---

## 📎 Keyboard Shortcuts and Help

* Expose accelerators with `GetKeyboardShortcut()`
* Provide help text via `GetHelpText()` or `GetDescription()`

---

## ✅ Code Review Checklist

Ensure each UI component:

* [ ] Is reachable via Tab
* [ ] Exposes a valid role
* [ ] Has an accessible name
* [ ] Reports dynamic changes via `NotifyEvent()`
* [ ] Keeps predictable focus flow

---

## 💡 Example Prompts

```python
# Prompt: Add wx.Accessible subclass for custom control with role=button
# Prompt: Set up a read-only TextCtrl that is still reachable via Tab
# Prompt: Call NotifyEvent on value change inside dynamic panel
# Prompt: Set logical focus when closing a modal dialog
```

---

*These instructions guide Copilot in generating inclusive wxPython applications by enforcing accessibility best practices.*
