# Frontend Development Prompt for Hospital Scheduler

**Role:** Expert Frontend Developer & UX/UI Designer
**Project:** Hospital Staff Scheduling Optimization Dashboard
**Tech Stack:** Next.js (App Router), React, Tailwind CSS, Shadcn UI, Recharts, Framer Motion, Lucide React.

## Project Overview

We are building a modern, high-performance dashboard for a **Hospital Staff Scheduling System**. The backend uses **Gurobi** (mathematical optimization) to generate optimal schedules for doctors and nurses, minimizing costs while ensuring all shifts are covered.

**Goal:** Create a "Wow" factor application that not only manages data but visualizes the optimization results effectively. The professor needs to be impressed by how the data is presented (charts, interactive calendars, smooth animations).

---

## API Integration Guide

The backend is running at `http://127.0.0.1:8000`. All endpoints are prefixed with `/api`.

### 1. Data Management (CRUD)

Users need to view and manage the resources before running a schedule.

-   **Employees** (`/api/employees`)
    -   `GET /`: List all employees.
    -   `POST /`: Create employee. Fields: `employee_id` (string), `name`, `role` (Nurse/Doctor), `skills` (e.g., "RN|ICU"), `hourly_cost` (float), `max_weekly_hours`.
    -   `DELETE /{id}`: Remove employee.
-   **Shifts** (`/api/shifts`)
    -   `GET /`: List shifts.
    -   `POST /`: Create shift. Fields: `shift_id`, `name` (Morning/Night), `start_time` ("07:00"), `end_time`, `length_hours`.
-   **Demands** (`/api/demands`)
    -   `GET /`: List staffing requirements.
    -   `POST /`: Add demand. Fields: `date` (YYYY-MM-DD), `shift_id`, `skill`, `required` (int).

### 2. Optimization Engine

-   **Seed Data** (`POST /api/test/seed`): A button to quickly populate the DB with sample data for demo purposes.
-   **Generate Schedule** (`POST /api/schedules`):
    -   Payload: `{ "horizon_start": "2025-11-29", "horizon_days": 7, "solver_time_limit": 60, "allow_uncovered_demand": true, "penalty_uncovered": 1000 }`
    -   Returns: `{ "run_id": "uuid...", "status": "QUEUED" }`
-   **Get Results** (`GET /api/schedules/{run_id}`):
    -   Poll this endpoint until `status` is "OPTIMAL" or "FEASIBLE".
    -   Returns: `assignments` list (who works when, cost, hours), `objective_value` (total cost score), and `logs`.

---

## Feature Requirements & Visualization Ideas

### 1. The "Wow" Dashboard (Home)

-   **Hero Section:** A clean, modern welcome screen.
-   **Quick Stats:** Cards showing "Total Employees", "Active Shifts", "Pending Demands".
-   **Action:** A prominent "Generate New Schedule" button that opens a wizard/modal.

### 2. Interactive Schedule Visualization (The Core Feature)

Once a schedule is generated, display the results in a stunning way:

-   **Calendar/Gantt View:** A visual grid (Rows = Employees, Columns = Days/Shifts). Use color coding for different shift types (Morning = Yellow, Night = Dark Blue).
-   **Interactive Tooltips:** Hovering over a shift block shows details (Shift Name, Hours, Cost).
-   **Filtering:** Allow filtering by Role (Nurse vs Doctor) or Skill.

### 3. Analytics & Charts (Recharts)

Showcase the "Optimization" part. Why is this schedule good?

-   **Cost Breakdown (Pie Chart):** Cost distribution by Role (How much are we spending on Nurses vs Doctors?).
-   **Workload Fairness (Bar Chart):** Hours assigned per employee. Show a reference line for "Max Hours" to prove constraints are met.
-   **Coverage Heatmap or Line Chart:** Demand vs. Supply. Show if any shifts are understaffed (uncovered demand).

### 4. Data Management Tables

-   Use **Shadcn UI Data Table** for Employees, Shifts, and Demands.
-   Include Search, Sort, and Pagination.
-   Add "Add New" dialogs for each resource.

### 5. UX/UI Polish

-   **Loading States:** When the solver is running (it takes time), show a cool "Optimizing..." animation (maybe a math/graph animation using Framer Motion).
-   **Toast Notifications:** Success/Error messages for API actions.
-   **Theme:** Professional Medical/SaaS theme. Clean whites, soft grays, and a primary accent color (e.g., Teal-600 or Blue-600).

---

## Implementation Strategy for v0

1.  **Start with the Layout:** Sidebar navigation (Dashboard, Employees, Shifts, Demands, Schedule Runs).
2.  **Build the "Results" Page first:** This is the most complex and impressive part. Mock the data if needed initially to get the visuals right.
3.  **Use Client Components:** For the interactive charts and calendar.
4.  **Error Handling:** Gracefully handle if the backend is offline or returns an error.

**Prompt for v0:**
"Build a comprehensive Hospital Scheduler Dashboard using Next.js, Tailwind, and Shadcn UI. It needs to consume a FastAPI backend. The key focus is on the 'Schedule Results' page: I need a visual calendar of assignments and Recharts graphs showing cost analysis and workload distribution. Use Framer Motion for smooth transitions. The app should look enterprise-grade but modern."
