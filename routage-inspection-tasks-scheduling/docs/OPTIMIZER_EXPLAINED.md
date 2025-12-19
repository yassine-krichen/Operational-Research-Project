OPTIMIZER_EXPLAINED
====================

This document explains in detail the routing optimizer used in this project: decision variables, objective function, all constraints, how Gurobi solves the model, how infeasibility is diagnosed, and tips for tuning and debugging. It provides enough detail to understand, modify, or extend the model.

Files to inspect in the project
- `optimizer.py`  — the MILP model builder and solver wrapper.
- `models.py`     — dataclasses for `Inspector`, `Task`, `Depot`, `RouteSolution`.
- `dataset_generator.py` — example datasets (inspectors, tasks, depot).
- `app.py`        — GUI; creates solver thread and consumes the solution.

1. Problem type (high level)
----------------------------
- Variant of Vehicle Routing Problem (VRP) / Multi-Depot (or multi-start) routing with:
  - Time windows
  - Skills matching (each task requires a skill; inspectors have skills)
  - Inspector availability windows and per-inspector work-hour caps
  - Route sequencing / service times
  - Objective: minimize travel time (plus small load-balancing penalty)

2. Decision variables
---------------------
Notation used here is aligned with the code but given in math form for clarity.

- x[i,j,k] ∈ {0,1}
  - x[i,j,k] = 1 if inspector k travels directly from node i to node j in his route.
  - Nodes include depot (index 0) and tasks (indices 1..n).

- y[i,k] ∈ {0,1}
  - y[i,k] = 1 if inspector k visits/serves task i (i is a task index; depot excluded).

- T[i,k] ≥ 0 (continuous)
  - arrival/start time of inspector k at node i.

- (Optional) z or M variables used for objective load balancing
  - e.g., max_tasks (an integer/continuous value) used to measure uneven workload; penalized in objective.

3. Objective function
---------------------
Objective = Minimize (total travel time) + λ * (load-balance penalty)

- Travel cost term: sum_{k} sum_{i} sum_{j} dist[i,j] * x[i,j,k]
  - `dist[i,j]` is the travel time (hours) between node i and j (Euclidean / speed). In the code it may be inspector-specific or shared.

- Load-balance term (small): λ * max_tasks_per_inspector
  - λ is a small coefficient (e.g., 0.1) used to push solver towards balanced assignments.
  - This is optional but included to avoid all tasks being assigned to one inspector when travel-only cost favors it.

4. Constraints (complete list & explanation)
--------------------------------------------
Below are the constraints you will find (or should expect) in `optimizer.py`. Names referenced are conceptual; the code uses programmatic names like `avail_end_{i}_{k}` or `no_self_loop_{i}_{k}`.

A. Task assignment (covering each task once)
- For every task i: sum_k y[i,k] == 1
  - Ensures each task is assigned to exactly one inspector.
  - If priority/optional tasks used, a variant sum_k y[i,k] >= 0 can be used; in this project tasks are mandatory.

B. Skill matching
- For task i and inspector k: if inspector k lacks required_skill(i) then y[i,k] == 0
  - Implemented in code by skipping feasible y variables or adding constraints y[i,k] ≤ skill_available_{i,k}.
  - Prevents assignment of an inspector who cannot perform the task.

C. Flow conservation (route validity)
- For each inspector k and each task node i:
  sum_j x[j,i,k] == sum_j x[i,j,k] == y[i,k]
  - If inspector k visits i (y[i,k]=1) then exactly one arc enters and one arc leaves i in k's route.
  - If y[i,k]=0 then in/out degrees are 0.

D. Depot start/end and route formation
- Each inspector route must start and end at the depot.
  - e.g., sum_j x[depot,j,k] == 1 (each inspector leaves the depot once) and sum_i x[i,depot,k] == 1 (returns once) for used inspectors.
  - In implementations where an inspector might be unused, these sums are conditional on whether inspector is active.

E. No self-loops
- For all i,k: x[i,i,k] == 0
  - Prevent traveling from a node to itself.

F. Time sequencing (Big‑M formulation)
- If x[i,j,k] == 1 then:
    T[j,k] ≥ T[i,k] + service_time(i) + travel_time(i,j)
  - Implemented as:
    T[j,k] ≥ T[i,k] + service_time(i) + travel_time(i,j) - BIGM * (1 - x[i,j,k])
  - When x[i,j,k] = 1, the Big-M term vanishes and the sequencing is enforced.
  - When x[i,j,k] = 0, the right-hand side becomes a very small number (−BIGM) so the constraint is inactive.

G. Time windows and inspector availability
- Each task i has a time window [tw_start_i, tw_end_i]. For assigned inspections:
    tw_start_i ≤ T[i,k] ≤ tw_end_i
  - Enforced with availability-checking constraints and Big-M when tasks are not assigned to a particular inspector:
    T[i,k] + service_time(i) ≤ tw_end_i + BIGM * (1 - y[i,k])
    T[i,k] ≥ tw_start_i - BIGM * (1 - y[i,k])

- Inspector availability: for inspector k with [avail_start_k, avail_end_k], tasks assigned to k must satisfy similar constraints:
    T[i,k] ≥ avail_start_k - BIGM*(1-y[i,k])
    T[i,k] + service_time(i) ≤ avail_end_k + BIGM*(1-y[i,k])

H. Work-hour caps (optional/aggregate)
- If the project enforces a per-inspector max_work_hours, a constraint ensures total time (travel + service) ≤ max_work_hours. This may be implemented as:
    sum assigned service_time + estimated travel_time ≤ max_work_hours
  - Often travel time is estimated by summing selected arcs' dist[i,j]*x[i,j,k].

I. Other logical constraints
- Prevent visiting tasks if unavailable, bound integers, optional balancing constraints:
  - max_tasks_per_inspector ≥ sum_i y[i,k] for all k; then minimize max_tasks_per_inspector or penalize in objective.

5. Big‑M: role and how to choose it
-----------------------------------
- Big‑M is used to make conditional (implicative) constraints linear using the x/y binary variables.
- Good M should be tight:
  - Too small M may incorrectly eliminate feasible solutions (infeasibility).
  - Too large M weakens lower bounds and increases solve time.
- A safe M for scheduling problems is sum of latest possible times (e.g., latest end-of-day) or an upper bound on route time (e.g., 24h or inspector availability span).

6. Gurobi solving process (how it works internally)
--------------------------------------------------
- Gurobi constructs the LP relaxation (drop integrality on binaries) and solves it to get a bound.
- It uses cutting planes, presolve, heuristics and branch-and-bound / branch-and-cut to find integer-feasible solutions.
- For big MILPs, you will see progress in the log: node count, incumbent objective, best bound, gap.
- Status codes you will encounter:
  - OPTIMAL: proven optimal solution
  - TIME_LIMIT or SUBOPTIMAL: best found solution within time limit
  - INFEASIBLE: no feasible solution exists for current model
  - UNBOUNDED: objective can be driven to −∞ (rare for routing if costs are positive)

7. Diagnosing infeasibility (IIS)
---------------------------------
- If Gurobi returns INFEASIBLE, call `model.computeIIS()`.
- Asking Gurobi for the IIS returns a small subset of constraints and variable bounds that are jointly infeasible.
- The code now runs `model.computeIIS()` and collects `constr.IISConstr` to print violating constraints. Typical names to inspect:
  - `assign_*` (assignment coverage)
  - `skill_*` (skill matching constraints)
  - `avail_start_*`, `avail_end_*` (availability/time windows)
  - `time_*` (sequencing)
  - `flow_*` (flow conservation)
- Use those names to determine root cause (e.g., insufficient skills, overlapping time windows, impossible travel sequences, or Big‑M problems).

8. How the solution is parsed and used in this project
------------------------------------------------------
- After solving the model, the code extracts x variables with value 1 to reconstruct routes per inspector.
- For each inspector k, the code finds arcs starting from depot and follows successive nodes j where x[i,j,k] == 1 to reconstruct the ordered route.
- It computes travel time and service time per inspector from the selected arcs and assigned tasks.
- The constructed `RouteSolution` objects (route list, travel_time, service_time) are returned to the GUI for visualization and reporting.

9. Practical debugging workflow
-------------------------------
1. Verify small instance (2 inspectors, 4 tasks) where you can reason manually.
2. If infeasible, call IIS and inspect constraint names — fix data (skills/time windows/availability) or relax constraints.
3. Visualize distances and inspector start positions; extremely distant inspectors may remain unused.
4. Tighten Big‑M: use realistic numeric bounds based on hours in the day or max route time.
5. Try relaxing the model (temporary removals) to locate the conflict, then restore constraints progressively.

10. Tuning knobs & suggestions
-------------------------------
- `TimeLimit`: reduce solve time for interactive GUI use, accept suboptimal solutions.
- `Balance weight (λ)`: increase to incentivize load spreading; set to 0 to minimize only travel time.
- `BIGM`: set to meaningful upper bound (e.g., day length 24h or a realistic max route time) rather than a very large 1e6.
- `Presolve` and `Cuts`: Gurobi defaults are good, but experiment with turning some on/off for hard instances.
- `Warm-start`: if you have a heuristic initial solution (e.g., greedy assignment), supply it to Gurobi to help search.

11. Example commands to run locally
----------------------------------
Run solver only (script `optimizer.py`):

```powershell
cd "c:\Users\akram\Desktop\RO project"
C:\Users\akram\AppData\Local\Programs\Python\Python311\python.exe optimizer.py
```

Run the GUI app (interactive):

```powershell
cd "c:\Users\akram\Desktop\RO project"
C:\Users\akram\AppData\Local\Programs\Python\Python311\python.exe app.py
```

12. Where to change parts of the model
-------------------------------------
- Variables/Objective: edit `optimizer.py` near the objective construction block.
- Constraints: `optimizer.py` where `model.addConstr(...)` or `model.addConstrs(...)` are used — adjust names and formulations there.
- Distances: `compute_distance_matrix()` in `optimizer.py` determines travel time between nodes (per inspector or shared depot).
- Load-balancing: look for the max_tasks variable and its penalty in the objective.

13. Quick checklist for common problems
--------------------------------------
- Tasks unassigned / inspector unused: check skills & depot vs inspector start location (or switch to shared depot).
- Model infeasible: run `computeIIS()`, inspect returned constraint names.
- Long solve times: try smaller instances, tighten BIG‑M, raise `TimeLimit` lower bound or relax objective.

-- End of document --
