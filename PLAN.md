# Project Migration Plan: React to PyQt

## 1. Overview

This plan outlines the migration of the Hospital Scheduler frontend from a web-based React application to a Python-based desktop application using **PyQt6**. The goal is to create a unified launcher interface for a group of 4 projects, with the Hospital Scheduler being one of the modules.

## 2. Architecture

The application will follow a **Modular Monolith** architecture.

-   **Launcher (`main.py`)**: The entry point containing the main menu with buttons for each of the 4 group projects.
-   **Hospital Scheduler Module (`projects/hospital_scheduler_gui/`)**: A self-contained package implementing the GUI for the scheduling problem.
-   **Shared Backend (`hospital_scheduler/app/`)**: The existing logic (Database, Models, Solver) will be reused directly by the GUI, bypassing the FastAPI layer to simplify the desktop deployment.

### Directory Structure

```
project/
├── desktop_app/                # NEW: The root of the desktop application
│   ├── main.py                 # Entry point (Launcher)
│   ├── assets/                 # Icons and styles
│   └── projects/               # Modules for each group member
│       ├── __init__.py
│       └── hospital_scheduler_gui/
│           ├── __init__.py
│           ├── main_window.py  # Dashboard for this specific project
│           ├── wizard.py       # Configuration input (Step-by-step)
│           ├── views/          # Sub-components
│           │   ├── calendar_view.py
│           │   ├── metrics_view.py
│           │   └── logs_view.py
│           └── workers.py      # Background threads for Gurobi solver
├── hospital_scheduler/         # EXISTING: Backend logic
│   ├── app/
│   │   ├── services/
│   │   ├── models.py
│   │   └── database.py
│   └── ...
└── ...
```

## 3. Implementation Steps

### Phase 1: Foundation & Launcher

1.  **Environment Setup**: Install `PyQt6` and `qdarktheme` (for modern UI).
2.  **Launcher Interface**: Create `desktop_app/main.py` with a clean, modern landing page featuring 4 large buttons.
    -   Button 1: "Hospital Staff Scheduler" (Active)
    -   Buttons 2-4: "Project X" (Placeholders)

### Phase 2: Hospital Scheduler GUI

1.  **Main Window**: Create the shell for the scheduler application with a navigation sidebar (Dashboard, History, Settings). [DONE]
2.  **Data Integration**: Connect `hospital_scheduler/app/database.py` to the GUI to fetch Employees and Shifts. [DONE]
3.  **Configuration Wizard**: Recreate the React "Schedule Wizard" using `QWizard` or a custom `QStackedWidget`. [DONE]
    -   Inputs: Date Range, Time Limit, Constraints (Sliders/SpinBoxes).
    -   Validation: Use Pydantic models from `schemas.py`.

### Phase 3: Solver Integration

1.  **Worker Thread**: Implement a `QThread` in `workers.py` to run `GurobiScheduler` without freezing the UI. [DONE]
    -   Signals: `started`, `finished`, `error`, `log_updated`.
2.  **Real-time Logs**: Redirect the solver's log buffer to a `QTextEdit` in the GUI. [DONE]

### Phase 4: Visualization

1.  **Calendar View**: Implement a custom `QTableWidget` or `QGraphicsView` to display the generated schedule. [DONE]
    -   Rows: Employees
    -   Columns: Days
    -   Cells: Color-coded shifts.
2.  **Metrics Dashboard**: Use `matplotlib` (embedded in PyQt) or simple `QProgressBar` widgets to show Cost, Uncovered Shifts, and Preference Violations. [PENDING]

## 4. Technical Details

### Database Connection

The GUI will use `SessionLocal` from `hospital_scheduler.app.database` to create a direct connection to the SQLite file.

### Solver Execution

Instead of calling the API, the GUI will:

1.  Collect parameters from the Wizard.
2.  Create a `SolveRequest` object.
3.  Instantiate `GurobiScheduler(db, run_id, params)`.
4.  Call `scheduler.solve()` in a background thread.

## 5. Future Proofing

-   The `projects/` folder structure allows other group members to drop in their own packages (e.g., `projects/transport_optimization/`) and simply add a button in `main.py` to launch their `MainWindow`.
