# QUICKSTART.md

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+
- Gurobi solver with valid license
- PyQt5, matplotlib

### Installation

```bash
pip install PyQt5 matplotlib gurobipy
```

---

## Usage Scenarios

### Scenario 1: Launch the Full-Featured GUI
```bash
python app.py
```

**What you get:**
- Interactive multi-tab interface
- Real-time optimization solver
- Inspector & task management
- Route visualization
- Detailed analytics

**Steps:**
1. Click "Dashboard" tab
2. Adjust time limit (10-300 seconds) if desired
3. Click "Solve Optimization"
4. View results in tabs:
   - **Dashboard**: Key metrics
   - **Routes Map**: Visual representation
   - **Analytics**: Detailed statistics

---

### Scenario 2: Manage Inspectors & Tasks

#### From the GUI (app.py):

**Add Inspector:**
1. Go to "Inspectors" tab
2. Click "Add Inspector"
3. Fill in ID, Name, Coordinates
4. Click OK

**Generate Random Inspectors:**
1. Go to "Inspectors" tab
2. Click "Generate Random"
3. Enter count (1-20)
4. View in table

**Add Task:**
1. Go to "Tasks" tab
2. Click "Add Task"
3. Fill in Name, Location, Duration, Skill
4. Click OK

**Generate Random Tasks:**
1. Go to "Tasks" tab
2. Click "Generate Random"
3. Enter count (1-50)
4. View in table

---

### Scenario 3: Optimize & Export

1. **Setup Data** (Inspectors/Tasks tabs)
2. **Solve** (Dashboard tab → "Solve Optimization")
3. **Export** (Dashboard tab → "Export Solution")
   - Saves to `.txt` file with full report
4. **View Routes** (Routes Map tab)
5. **Analyze** (Analytics tab)

---

### Scenario 4: Command-Line Testing

**Test optimizer directly:**
```bash
python optimizer.py
```

Output:
```
============================================================
INSPECTION ROUTING OPTIMIZATION
============================================================

Dataset: 3 inspectors, 10 tasks
...
ROUTES BY INSPECTOR
---
I1:
  Route: [0, 1, 4, 8, 0]
  Travel Time: 1.23 h
  ...
```

**Generate and solve programmatically:**
```python
from dataset_generator import DatasetGenerator
from optimizer import solve_routing

# Create data
inspectors, tasks, depot = DatasetGenerator.generate_dataset(num_inspectors=5, num_tasks=15)

# Solve
solution = solve_routing(inspectors, tasks, depot, time_limit=30)

# Print summary
print(solution.summary())
```

---

### Scenario 5: Load/Create Custom Data

**Load sample data:**
- Launch `app.py`
- File Menu → "Load Sample Dataset"

**Create custom data:**
1. **Inspectors tab** → "Add Inspector" (manual) or "Generate Random"
2. **Tasks tab** → "Add Task" (manual) or "Generate Random"
3. Configure skills and time windows
4. **Dashboard tab** → "Solve Optimization"

---

### Scenario 6: Export Solutions

**From GUI:**
1. Solve the problem (Dashboard tab)
2. Click "Export Solution"
3. Choose filename (e.g., `solution.txt`)
4. Opens system default viewer or text editor

**Programmatically:**
```python
from utils import DataExporter

# Export in multiple formats
DataExporter.export_solution_json(solution, "solution.json")
DataExporter.export_routes_csv(solution, "routes.csv")
DataExporter.export_report_txt(solution, inspectors, tasks, "report.txt")
```

---

## Typical Workflow

### For Quick Testing:
```bash
python optimizer.py              # 30 seconds
# See routes printed in console
```

### For Interactive Use:
```bash
python app.py                    # Launch GUI
# Use Dashboard → Solve → View results
```

### For Automation:
```python
from dataset_generator import DatasetGenerator
from optimizer import solve_routing
from utils import DataExporter

# Generate, solve, export in one script
inspectors, tasks, depot = DatasetGenerator.generate_dataset(num_inspectors=3, num_tasks=10)
solution = solve_routing(inspectors, tasks, depot, time_limit=60)
DataExporter.export_report_txt(solution, inspectors, tasks, "report.txt")
```

---

## Common Tasks

| Task | Method |
|------|--------|
| Generate 20 random tasks | Tasks tab → "Generate Random" → 20 |
| Add a specific inspector | Inspectors tab → "Add Inspector" |
| View optimal routes on map | Routes Map tab → "Refresh Map" |
| Get performance statistics | Analytics tab → "Refresh Analytics" |
| Export full report | Dashboard → "Export Solution" |
| Change solver time limit | Dashboard → Adjust "Time Limit (s)" |
| See all metrics | Analytics tab (full breakdown) |
| Check inspector utilization | Analytics tab (shows % per inspector) |

---

## Tips & Tricks

1. **Large instances** (>50 tasks): Increase time limit to 120-300 seconds
2. **Real-time feedback**: Check Status Log in Dashboard for progress
3. **Route quality**: More solver time = better solutions (diminishing returns after ~120s)
4. **Rerun optimization**: Just click "Solve" again with different settings
5. **Compare solutions**: Export solutions with different parameters and compare

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError: No module named 'gurobipy'" | Install Gurobi: `pip install gurobipy` + get license |
| No solution after optimization | Check if all tasks can be assigned (skill mismatch?) |
| App crashes on large dataset | Reduce problem size or increase time limit gradually |
| Map not showing routes | Click "Refresh Map" button, ensure solution exists |

---

## File Outputs

When you export a solution, you get a `.txt` file with:
- Solver summary (objective, time, status)
- Inspector list with skills & availability
- Task list with details
- Detailed routes per inspector
- Inspector utilization percentages

---

**For more detailed information, see `README.md`**
