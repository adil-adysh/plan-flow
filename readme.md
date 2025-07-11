
# PlanFlow: Accessible Task Scheduling for NVDA (In Development)

**PlanFlow** is an NVDA add-on designed to help you schedule, track, and manage your daily tasks in an accessible way. The project is under active development—some features are available now, and many more are planned.

> **Note for Users:** There is currently no user interface. All features are accessible only via Python code or scripts. If you are an end user, you may want to follow the project for updates as we work toward a full, user-friendly experience.

---

## What Can PlanFlow Do Right Now?

- **Add and Store Tasks:** Create tasks with a title, description, and scheduled time (using code).
- **Recurring Tasks:** Set up tasks to repeat on a regular schedule (e.g., daily, weekly).
- **Time Slots and Working Hours:** Define your preferred time slots (like “morning” or “evening”) and set your working hours for each day.
- **Daily Task Limits:** Limit how many tasks can be scheduled per day.
- **Mark Tasks as Done:** Mark tasks as done and keep a history of completions.
- **Automatic Handling of Missed Tasks:** Missed tasks can be automatically rescheduled according to your preferences and limits.
- **Local Storage:** All your data is stored locally on your computer. Nothing is sent online.

---

## What’s Coming Next?

- **User Interface:** A simple, accessible interface for managing your tasks directly from NVDA.
- **Notifications and Reminders:** Get notified when tasks are due or missed.
- **Settings and Customization:** More options for customizing your experience.
- **Better Documentation:** Step-by-step guides and help resources.

---

## For Developers: Get Involved!


PlanFlow is open source and welcomes contributions. If you’re interested in accessible technology, task management, or NVDA add-ons, we’d love your help!

## 📚 Documentation

- [Task Design](docs/task-design.md): Core scheduling and model concepts
- [TODOs](TODO.md): Current priorities, open tasks, and ideas
- [Test Plans](tests/): Test coverage and scenarios
- [Instructions](.github/instructions/): Module-level implementation rules


**How to Contribute:**
  - Please read the [Task Design](docs/task-design.md) for the core design and architecture before contributing.
  - Review the [TODOs](TODO.md) for current priorities and open tasks.
  - Each test file has a corresponding `testplan.md` in the `tests/` folder, describing the test coverage and scenarios for that module. Review these to understand the test strategy and expectations.
  - See the issues list for bugs and feature requests.
  - Submit pull requests for improvements, new features, or bug fixes.
  - Help us test and document the add-on.

- **Tech Stack:**
  - Python 3.11+
  - TinyDB for local storage
  - Fully typed, testable, and NVDA-independent core logic
  - Pytest, Ruff, and Pyright for testing and code quality

- **Contact:**
  - Join the NVDA add-on community or open an issue in the repository.

---

Thank you for your interest in PlanFlow!

*This project is a work in progress. Follow along for updates and new features, and consider joining us to help build the future of accessible task management.*
