
# ✅ PlanFlow Roadmap & TODOs 
---

## 🔹 MVP First Milestone: Basic NVDA Add-on with Manual Task Creation

> 🎯 Goal: Press shortcut → Enter task → Get spoken confirmation
> This unlocks testing PlanFlow as a *real* tool, even before AI or calendar views.

### Phase 1: NVDA Add-on Entry & Binding (Foundational)

* [ ] Register NVDA keyboard shortcut (e.g., `Ctrl+Alt+T`)
* [ ] Open basic dialog box:

  * [ ] Input fields: Task title (mandatory), description (optional)
  * [ ] Buttons: OK / Cancel
* [ ] On OK:

  * [ ] Save task via `ExecutionRepository`
  * [ ] Schedule with `SmartSchedulerService`
  * [ ] NVDA speaks: "Task created"
* [ ] On Cancel: NVDA speaks "Cancelled"
* [ ] Test: Add-on loads, shortcut works, dialog appears

---

## 🔁 Phase 2: Task Execution & Speech Output

Once tasks can be created, we should confirm they run and NVDA speaks the output.

* [ ] When a task is triggered: speak its title
* [ ] When task retry or recurrence is scheduled: optional speech
* [ ] Error speech if scheduling fails or required field missing

> 🧪 Ensures core PlanFlow backend is wired to NVDA output
> No browsing tasks yet—just real-time feedback.

---

## 🗣️ Phase 3: Commands to Browse Tasks via NVDA

Once scheduling and speaking work, we can let users *query* tasks.

* [ ] NVDA command: Speak today’s tasks
* [ ] NVDA command: Speak missed tasks
* [ ] NVDA command: Speak upcoming tasks
* [ ] Format output for clarity and shortness (NVDA-friendly)

---

## 🧠 Phase 4: AI-Powered Task Creation (Cloud + Offline)

Once manual input works reliably, unlock fast task creation via AI.

### Gemini API (Cloud)

* [ ] Input: user says or types "remind me to call mom tomorrow"
* [ ] Parse via Gemini
* [ ] Create task based on response
* [ ] Handle API errors or slow response

### Gemma3n (Offline Fallback)

* [ ] Detect offline mode
* [ ] Use Gemma3n locally to do the same
* [ ] Match behavior with Gemini as closely as possible

---

## 🛠️ Phase 5: Tooling and Automation

Improve dev velocity and transparency.

* [ ] Custom logger

  * [ ] Log levels (debug/info/error)
  * [ ] Optional no-log mode for end users
* [ ] Sync `TODO.md` ↔ GitHub Issues (using GitHub Actions)

  * [ ] Parse checklists and update issues

---

## 📦 Phase 6: Packaging & Distribution

Enable non-dev users to install PlanFlow easily.

* [ ] Package as NVDA-compatible `.nvda-addon` (primary path)
* [ ] Research PyInstaller or py2exe (for standalone)
* [ ] Manual install instructions for devs and power users

---

## 🔮 Phase 7: UI Extensions (Post-MVP)

After all above works, extend experience with calendar logic.

* [ ] Calendar view by day/week/month (tree or list structure)
* [ ] Task editing UI
* [ ] Task drag/move or reschedule
* [ ] Delete/Mark task done with shortcut or context menu

---

## 👋 Good First Issues

Tag these in GitHub to help new contributors:

* [ ] Register NVDA shortcut and open dialog
* [ ] Save entered task and confirm with speech
* [ ] Speak today’s tasks via NVDA command
* [ ] Add simple integration test for dialog → schedule

---

## ✅ Reminder: What’s Already Done

These need **no work**:

* ✅ SmartSchedulerService: task execution, retries, recurrence
* ✅ ExecutionRepository with all persistence logic
* ✅ CalendarPlanner + working hours logic
* ✅ RecoveryService for missed tasks
* ✅ Unit & integration tests
