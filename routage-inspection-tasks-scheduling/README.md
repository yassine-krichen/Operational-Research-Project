# Inspection Routing Optimization System - Project Structure

## Overview
A **multi-inspector routing optimization system** for planning security and quality inspections using Gurobi MILP (Mixed-Integer Linear Programming). The system automatically assigns inspection tasks to inspectors while respecting skills, time windows, and availability constraints.

## Project Modules

### 1. **models.py** - Data Models
Defines clean data structures using Python dataclasses:
- `Inspector`: Skills, availability, work constraints
- `Task`: Location, duration, skill requirement, time windows, difficulty, priority
- `Depot`: Starting/ending location
- `RouteSolution`: Solution for one inspector's route
- `SolutionResult`: Complete solution with all routes and metrics

**Benefits**: Type safety, easy serialization, clear API contracts

---

### 2. **dataset_generator.py** - Data Generation
Generates realistic inspection scheduling datasets:
- **`DatasetGenerator.generate_inspectors()`**: Random or structured inspectors with skills, locations, availability
- **`DatasetGenerator.generate_tasks()`**: Tasks with varying difficulty levels (1-5), skills, time windows
- **`DatasetGenerator.generate_dataset()`**: Complete dataset with inspectors, tasks, and depot

**Features**:
- Difficulty multipliers (affects task complexity)
- Skill pool management
- Reproducible random generation (optional seed)
- Structured vs. random modes for testing

---

### 3. **optimizer.py** - MILP Solver
Gurobi-based optimization engine for the inspection routing problem:

**`compute_distance_matrix()`**
- Euclidean distance calculation in hours
- Handles inspectors, tasks, and depot locations
- Configurable travel speed

**`solve_routing(inspectors, tasks, depot, time_limit, speed_kmh)`**
- Builds complete Gurobi MILP model
- **Decision Variables**:
  - `x[i,j,k]`: Binary (inspector k travels from i to j)
  - `y[i,k]`: Binary (inspector k visits task i)
  - `T[i,k]`: Continuous (arrival time at task i)

- **Constraints** (9 types):
  1. Each task assigned to exactly one inspector
  2. Flow conservation for each inspector
  3. Depot departure/return rules
  4. Skill compatibility filtering
  5. Time sequencing with Big-M
  6. Time window enforcement
  7. Work hours per inspector
  8. No self-loops
  9. Inspector availability windows

- **Objective**: Minimize total travel time

**Output**: `SolutionResult` with routes, metrics, solver status

---

### 4. **main.py** - GUI Application
PyQt5-based user interface for the inspection routing system:

**Features**:
- Data loading and display
- Solver integration with progress feedback
- Route table visualization
- Interactive map plotting with matplotlib
- Error handling with user-friendly messages

**Workflow**:
1. Load Data → displays inspector/task counts
2. Solve → calls optimizer, shows objective value
3. Show Routes → plots routes on map with color-coding

---

## Project Context: PLNE/PLM
**Planification des Inspections de Sécurité ou de Qualité** (Planning Security or Quality Inspections)  
**Routage du Personnel** (Personnel Routing)

This is a **Vehicle Routing Problem (VRP)** variant solved with PLNE (**Programmation Linéaire en Nombres Entiers** = Integer Linear Programming).

---

## Installation & Dependencies

```bash
pip install PyQt5 matplotlib gurobipy
```

**Note**: Gurobi requires:
- Gurobi solver installation
- Valid license (academic or commercial)

---

## Usage

### Standalone (Test Optimizer)
```bash
python optimizer.py
```
Runs the solver with default structured dataset and prints route summary.

### GUI Application (Legacy Single Window)
```bash
python main.py
```
Launches the original PyQt5 interface.

### Multi-Tab Application (New)
```bash
python app.py
```
Launches the comprehensive multi-tab interface with full feature set.

---

## Key Improvements Over Previous Version

| Aspect | Before | After |
|--------|--------|-------|
| **Structure** | Monolithic, hardcoded data | Modular, reusable components |
| **Data Models** | Dictionaries (untyped) | Dataclasses (typed, validated) |
| **Dataset Gen** | Fixed data only | Flexible generator (random/structured) |
| **Distance Calc** | Embedded in optimizer | Separate utility function |
| **Solution Format** | Basic dict | Rich `SolutionResult` object with metrics |
| **Extensibility** | Low | High (easy to add features, constraints) |
| **Testing** | Hard to test parts | Easy unit testing per module |

---

## Future Enhancements

1. **Multi-objective optimization** (travel time + fairness + priority)
2. **Dynamic task insertion** (real-time scheduling)
3. **Constraint relaxation** (soft constraints with penalties)
4. **Heuristic comparison** (Gurobi vs. genetic algorithms)
5. **Export/reporting** (PDF route reports, performance analytics)
6. **REST API** (cloud-based optimization service)

---

## File Organization

```
RO project/
├── models.py              # Data structures (Inspector, Task, Depot, SolutionResult)
├── dataset_generator.py   # Dataset generation utilities
├── optimizer.py           # MILP solver (Gurobi)
├── utils.py               # Data import/export utilities
├── main.py                # Legacy single-window PyQt5 GUI
├── app.py                 # Multi-tab comprehensive GUI application
├── frontend.ui            # Qt Designer UI file (legacy)
└── README.md              # This file
```

## Multi-Tab GUI Features (app.py)

### 1. Dashboard Tab
- **Solver Controls**: Time limit, travel speed configuration
- **Real-time Optimization**: Background solving with progress feedback
- **Solution Metrics**: Live display of objective value, travel/service times
- **Status Logging**: Timestamped event log
- **Export**: Save solutions to text files

### 2. Inspector Management Tab
- **Inspector Table**: View all inspectors with details
- **Add/Delete**: Manual inspector management
- **Random Generation**: Bulk generate random inspectors
- **Columns**: ID, Name, Skills, Max Hours, Location, Availability

### 3. Task Management Tab
- **Task Table**: View all tasks with full details
- **Add/Delete**: Manual task management
- **Random Generation**: Bulk generate random tasks
- **Columns**: ID, Name, Location, Duration, Skill, Difficulty, Time Window, Priority

### 4. Routes Visualization Tab
- **Interactive Map**: Plot all inspector routes with color coding
- **Depot Highlighting**: Red marker for depot location
- **Task Markers**: Blue dots with task IDs
- **Route Lines**: Colored lines per inspector with proper sequencing

### 5. Analytics & Statistics Tab
- **Summary Metrics**: Total travel time, service time, objective value
- **Route Statistics**: Tasks assigned, number of active routes
- **Workload Analysis**: Per-inspector breakdown
- **Inspector Utilization**: Percentage of max work hours used
- **Detailed Route Info**: Full route sequences with timings

---

## Example: Using the System Programmatically

```python
from dataset_generator import DatasetGenerator
from optimizer import solve_routing
from utils import DataExporter

# Generate dataset
inspectors, tasks, depot = DatasetGenerator.generate_dataset(
    num_inspectors=5,
    num_tasks=20,
    structured=False,  # Random generation
    seed=42
)

# Solve
solution = solve_routing(inspectors, tasks, depot, time_limit=60)

# Print results
print(solution.summary())

# Export in multiple formats
DataExporter.export_solution_json(solution, "solution.json")
DataExporter.export_routes_csv(solution, "routes.csv")
DataExporter.export_report_txt(solution, inspectors, tasks, "report.txt")

# Print per-inspector details
for ins_id, route_sol in solution.routes.items():
    print(f"{ins_id}: Route {route_sol.route}, "
          f"Travel: {route_sol.travel_time:.2f}h, "
          f"Tasks: {route_sol.tasks_completed}")
```

---

## Notes

- All time values are in **hours** (0-24)
- Coordinates are unitless (relative positions)
- Travel speed defaults to 40 km/h
- Gurobi optimizer has a time limit (default 60 seconds)
- Larger instances (>100 tasks, >10 inspectors) may benefit from fine-tuning Gurobi parameters
