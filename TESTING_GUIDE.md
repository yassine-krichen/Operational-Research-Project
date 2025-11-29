# Quick Start Guide - Testing the System

## Prerequisites

-   Backend running: `cd hospital_scheduler && .\.venv\Scripts\activate && uvicorn app.main:app --reload`
-   Frontend running: `cd hospital-scheduler-dashboard && npm run dev`
-   Both services listening on correct ports (backend: 8000, frontend: 3000)

## Testing Workflow

### 1️⃣ Seed Demo Data

**Location**: Dashboard page (/)
**Steps**:

1. Open http://localhost:3000/
2. Click "Seed Demo Data" button
3. Toast notification confirms: "Sample data loaded successfully!"
4. Page will reload automatically

**Expected**: Employees, Shifts, Demands pages now show real data from backend

---

### 2️⃣ View Employees

**Location**: Employees page (/employees)
**Expected**:

-   List of 5 employees (doctors and nurses)
-   Each shows: ID, name, role, skills, cost, max hours
-   "Add Employee" button works
-   Delete functionality works

**Verify API**: DevTools → Network → Filter to "localhost:3000"

-   Should see requests to `http://127.0.0.1:8000/api/employees`
-   NOT `http://localhost:3000/api/employees`

---

### 3️⃣ View Shifts

**Location**: Shifts page (/shifts)
**Expected**:

-   3 shift types (S1, S2, S3)
-   Morning, Afternoon, Night shifts
-   Start/end times and duration shown

---

### 4️⃣ View Demands

**Location**: Demands page (/demands)
**Expected**:

-   Multiple staffing requirements by date and shift
-   Shows which skill is needed (RN, MD, ICU, etc.)
-   Number of staff required

---

### 5️⃣ Generate Schedule (Main Test)

**Location**: Dashboard page (/) OR Schedule Runs page (/schedules)
**Steps**:

1. Click "Generate Schedule" button
2. **Step 1 - Schedule Period**:

    - Pick a start date (e.g., today)
    - Set duration to 7 days
    - Click "Next"

3. **Step 2 - Solver Settings**:

    - Solver Time Limit: 60 seconds
    - Allow Uncovered Demand: ON (toggle)
    - Uncovered Penalty: 1000
    - Click "Next"

4. **Step 3 - Review & Generate**:

    - Review all settings
    - Click "Generate Schedule"

5. **Observe**:

    - OptimizationLoader appears with progress animation
    - Shows stages: "Loading constraints", "Running optimization", "Analyzing results", "Finalizing schedule"
    - Progress bar fills to 100%

6. **When Complete**:
    - Schedule results display
    - See: Status badge, total cost, calendar view, charts
    - ScheduleCalendar shows employee assignments
    - CostChart shows cost breakdown by role
    - WorkloadChart shows hours per employee vs limits

---

### 6️⃣ Schedule Runs History

**Location**: Schedule Runs page (/schedules)
**Expected**:

-   Left panel: List of all generated schedules
-   Shows: ID (truncated), creation time, status icon, status badge
-   Click any schedule to view its details
-   Right panel shows: Details + Charts/Calendar tabs

---

## Validation Checklist

### Network Validation ✅

```
DevTools → Network tab → Generate a schedule

Should see requests like:
✅ POST http://127.0.0.1:8000/api/schedules
   Response: { "run_id": "...", "status": "QUEUED" }

✅ GET http://127.0.0.1:8000/api/schedules/{run_id}
   Response: { "run_id": "...", "status": "QUEUED|RUNNING|OPTIMAL", "assignments": [...], ... }

✅ Polling continues until status is not RUNNING/QUEUED
```

### Data Validation ✅

```
Assignment should have ALL fields:
✅ employee_id: "E1"
✅ employee_name: "Dr. Johnson"         (enriched from API)
✅ role: "Doctor"                       (enriched from API)
✅ date: "2025-12-01"
✅ shift_id: "S1"
✅ shift_name: "Morning"                (enriched from API)
✅ hours: 8.0
✅ cost: 200.0
```

### Display Validation ✅

```
ScheduleCalendar:
✅ Shows employee names on left
✅ Shows date row with days and dates
✅ Shows colored shift blocks for assignments

CostChart:
✅ Pie chart breakdown by role (Doctor, Nurse, etc)
✅ Shows percentages
✅ Total cost displayed below

WorkloadChart:
✅ Horizontal bar chart
✅ Employee names on left
✅ Hours on x-axis with max hour reference line
✅ Red bars for employees over max
```

---

## Troubleshooting

### "Failed to create schedule" Error

-   ✅ Backend running? Check `http://127.0.0.1:8000/docs`
-   ✅ CORS enabled? Should be in main.py
-   ✅ API URL correct? Check `.env.local`: `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api`

### "No assignments generated" or Empty Results

-   ✅ Did you seed data first? Click "Seed Demo Data"
-   ✅ Check browser console for errors
-   ✅ Backend logs should show "Solution found: X assignments"

### Requests going to localhost:3000/api instead of backend

-   ❌ This means `useApi` hook not being used properly
-   ✅ Verify page imports: `import { useApi } from "@/lib/use-api"`
-   ✅ Verify hook usage: `const { data } = useApi("/endpoint")`

### Gurobi License Issue

-   ❌ "Gurobi Error: Invalid license" in backend logs
-   ✅ Install free academic license: https://www.gurobi.com/academia/academic-program-and-licenses/
-   ✅ Or install evaluation license for testing

### Dates don't match

-   Ensure SolveRequest.horizon_start is sent as string: "2025-12-01" format
-   Backend queries Demand.date >= start, < start + horizon_days

---

## Performance Notes

-   First request may take 2-3 seconds (SWR cache revalidation)
-   Schedule optimization time depends on:

    -   Number of employees
    -   Number of shifts
    -   Schedule horizon (days)
    -   Solver time limit (set in wizard)
    -   Current system load

-   Typical times with demo data:
    -   7-day horizon: 5-10 seconds
    -   14-day horizon: 15-30 seconds
    -   28-day horizon: 45-60 seconds (if time limit is 60s)

---

## Success Criteria

✅ All tests pass if:

1. Seed Data button works and page shows real data
2. All CRUD pages show real backend data
3. Schedule generation completes without errors
4. Assignments display with employee names and shift names
5. Charts show meaningful data
6. Network tab shows all requests to `127.0.0.1:8000/api`
7. No relative URLs like `/api/...` appear in Network tab

🎉 System is production-ready for demo!
