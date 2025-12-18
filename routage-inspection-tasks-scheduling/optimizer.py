"""
Multi-Inspector Routing Optimizer using Gurobi MILP.
Solves the inspection scheduling problem to minimize travel time
while respecting skill requirements, time windows, and inspector availability.
"""

import math
import time
from typing import List, Dict, Optional
import gurobipy as gp
from gurobipy import GRB

from models import Inspector, Task, Depot, RouteSolution, SolutionResult


def compute_distance_matrix(
    inspectors: List[Inspector],
    tasks: List[Task],
    depot: Depot,
    speed_kmh: float = 40.0,
    use_depot_start: bool = False,
) -> Dict:
    """
    Compute Euclidean travel time matrices in hours.
    Each inspector has their own distance matrix based on their individual starting location.
    
    Args:
        inspectors: List of inspectors
        tasks: List of tasks
        depot: Depot location (used for return point)
        speed_kmh: Travel speed in km/h
    
    Returns:
        Dict with distance matrices and node indexing
    """
    m_inspectors = len(inspectors)
    num_tasks = len(tasks)
    n = 1 + num_tasks  # 1 (start/depot) + tasks

    # If use_depot_start is True, build a single distance matrix using the depot
    # as node 0 and duplicate it for all inspectors. Otherwise build per-inspector
    # matrices where node 0 is the inspector's own starting location.
    distance = []

    if use_depot_start:
        locations = [(depot.x, depot.y)]
        for task in tasks:
            locations.append((task.x, task.y))

        dist = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    dist[i][j] = 0.0
                else:
                    dx = locations[i][0] - locations[j][0]
                    dy = locations[i][1] - locations[j][1]
                    euclidean = math.sqrt(dx * dx + dy * dy)
                    dist[i][j] = euclidean / speed_kmh

        distance = [dist for _ in range(m_inspectors)]
    else:
        # per-inspector matrices (start at inspector.location)
        for inspector in inspectors:
            locations = [(inspector.location[0], inspector.location[1])]
            for task in tasks:
                locations.append((task.x, task.y))

            dist = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    if i == j:
                        dist[i][j] = 0.0
                    else:
                        dx = locations[i][0] - locations[j][0]
                        dy = locations[i][1] - locations[j][1]
                        euclidean = math.sqrt(dx * dx + dy * dy)
                        dist[i][j] = euclidean / speed_kmh

            distance.append(dist)
    
    return {
        "distance": distance,  # List of per-inspector matrices
        "num_nodes": n,
        "num_inspectors": m_inspectors,
        "task_ids": [task.id for task in tasks],
        "inspectors": inspectors,  # Include for reference
    }


def solve_routing(
    inspectors: List[Inspector],
    tasks: List[Task],
    depot: Depot,
    time_limit: int = 60,
    speed_kmh: float = 40.0,
    use_depot_start: bool = False,
) -> SolutionResult:
    """
    Solve the multi-inspector routing problem using Gurobi MILP.
    
    Args:
        inspectors: List of available inspectors
        tasks: List of tasks to schedule
        depot: Depot/starting location
        time_limit: Gurobi time limit in seconds
        speed_kmh: Travel speed for distance calculation
    
    Returns:
        SolutionResult with routes and metrics
    """
    start_time = time.time()
    
    # Compute distance matrix
    dist_data = compute_distance_matrix(inspectors, tasks, depot, speed_kmh, use_depot_start)
    dist = dist_data["distance"]
    n = dist_data["num_nodes"]  # depot + tasks
    m_inspectors = len(inspectors)
    
    # Create Gurobi model
    model = gp.Model("inspection_routing")
    model.setParam("TimeLimit", time_limit)
    model.setParam("OutputFlag", 0)  # Silent mode
    
    # Decision variables
    # x[i, j, k] = 1 if inspector k travels from node i to node j
    x = model.addVars(n, n, m_inspectors, vtype=GRB.BINARY, name="x")
    
    # y[i, k] = 1 if inspector k visits node i (task)
    y = model.addVars(n, m_inspectors, vtype=GRB.BINARY, name="y")
    
    # T[i, k] = arrival time at node i for inspector k
    T = model.addVars(n, m_inspectors, lb=0.0, ub=24.0, name="T")
    
    # Objective: minimize total travel time with light load-balancing incentive
    # Encourages spreading tasks across inspectors without complex quadratic terms
    # Now uses inspector-specific distances
    travel_cost = gp.quicksum(
        dist[k][i][j] * x[i, j, k]
        for i in range(n)
        for j in range(n)
        for k in range(m_inspectors)
    )
    
    # Simple load balancing: penalize max tasks assigned to any one inspector
    # Create auxiliary variable for max tasks assigned to any inspector
    max_tasks_inspector = model.addVar(ub=n-1, name="max_tasks_inspector")
    for k in range(m_inspectors):
        model.addConstr(
            gp.quicksum(y[i, k] for i in range(1, n)) <= max_tasks_inspector,
            name=f"max_tasks_bound_{k}"
        )
    
    # Objective: minimize travel + penalty for unbalanced load
    # Small penalty coefficient so travel is still primary objective
    obj = travel_cost + 0.1 * max_tasks_inspector
    model.setObjective(obj, GRB.MINIMIZE)
    
    # Constraints
    depot_idx = 0
    
    
    
    # (1) Each task is assigned to exactly one inspector
    for i in range(1, n):
        model.addConstr(
            gp.quicksum(y[i, k] for k in range(m_inspectors)) == 1,
            name=f"assign_task_{i}"
        )
    
    # (2) Flow constraints: conservation of flow for TASK nodes only
    # The depot (node 0) is handled separately in constraint (3)
    for k in range(m_inspectors):
        for i in range(1, n):  # Only for task nodes (1 to n-1), not depot
            model.addConstr(
                gp.quicksum(x[i, j, k] for j in range(n)) == y[i, k],
                name=f"flow_out_{i}_{k}"
            )
            model.addConstr(
                gp.quicksum(x[j, i, k] for j in range(n)) == y[i, k],
                name=f"flow_in_{i}_{k}"
            )
    
    # (3) Depot constraints: each inspector must depart and return to their starting location exactly once
    # Note: Node 0 is now their starting location (not a shared depot)
    for k in range(m_inspectors):
        # Number of tasks assigned to inspector k
        num_tasks_k = gp.quicksum(y[i, k] for i in range(1, n))
        
        # If inspector has tasks, must exit their location exactly once
        model.addConstr(
            gp.quicksum(x[depot_idx, j, k] for j in range(1, n)) == num_tasks_k,
            name=f"start_depart_if_tasks_{k}"
        )
        
        # If inspector has tasks, must return to their location exactly once
        model.addConstr(
            gp.quicksum(x[i, depot_idx, k] for i in range(1, n)) == num_tasks_k,
            name=f"start_return_if_tasks_{k}"
        )
    
    # (4) Skill compatibility: inspector k can only visit task i if k has the required skill
    for k, inspector in enumerate(inspectors):
        for i in range(1, n):
            task = tasks[i - 1]
            if task.required_skill not in inspector.skills:
                model.addConstr(y[i, k] == 0, name=f"skill_mismatch_{i}_{k}")
    
    # (5) Time/sequencing constraints with Big-M
    # Only apply to edges between task nodes or from/to inspector starting location
    BIGM = 1e4
    for k in range(m_inspectors):
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                
                # Skip self-loops at starting location
                if i == depot_idx and j == depot_idx:
                    continue
                
                # Get inspector-specific travel time
                travel_time = dist[k][i][j]
                
                # For edges involving inspector starting location (node 0)
                if i == depot_idx:  # Departing from inspector's starting location to task j
                    model.addConstr(
                        T[j, k] >= 0 + travel_time - BIGM * (1 - x[i, j, k]),
                        name=f"time_seq_{i}_{j}_{k}"
                    )
                elif j == depot_idx:  # Returning to inspector's starting location from task i
                    service_time = tasks[i - 1].duration
                    # No constraint on T[starting location] when returning
                    continue
                else:  # Both i and j are tasks
                    service_time = tasks[i - 1].duration
                    model.addConstr(
                        T[j, k] >= T[i, k] + service_time + travel_time - BIGM * (1 - x[i, j, k]),
                        name=f"time_seq_{i}_{j}_{k}"
                    )
    
    # (6) Time window constraints
    for k in range(m_inspectors):
        for i in range(n):
            if i == depot_idx:
                continue
            
            task = tasks[i - 1]
            
            model.addConstr(
                T[i, k] >= task.tw_start - BIGM * (1 - y[i, k]),
                name=f"tw_lower_{i}_{k}"
            )
            model.addConstr(
                T[i, k] + task.duration <= task.tw_end + BIGM * (1 - y[i, k]),
                name=f"tw_upper_{i}_{k}"
            )
    
    # (7) Inspector work-hours and availability constraints
    # Ensure tasks are completed by end of availability window
    for k, inspector in enumerate(inspectors):
        for i in range(1, n):
            task = tasks[i - 1]
            model.addConstr(
                T[i, k] + task.duration <= inspector.availability_end + BIGM * (1 - y[i, k]),
                name=f"avail_end_{i}_{k}"
            )
    
    # (7b) Enforce total route duration within availability window
    # Total time = (last return to depot time) - (first departure from depot)
    # Must fit within availability window
    for k, inspector in enumerate(inspectors):
        # Calculate total travel + service time for this inspector
        total_time = gp.quicksum(
            dist[k][i][j] * x[i, j, k] 
            for i in range(n) for j in range(n)
        ) + gp.quicksum(
            tasks[i - 1].duration * y[i, k] 
            for i in range(1, n)
        )
        
        # Total route time must fit within availability window
        max_route_duration = inspector.availability_end - inspector.availability_start
        model.addConstr(
            total_time <= max_route_duration,
            name=f"total_route_duration_{k}"
        )
    
    # (8) No self-loops
    for k in range(m_inspectors):
        for i in range(n):
            model.addConstr(x[i, i, k] == 0, name=f"no_self_loop_{i}_{k}")
    
    # (9) Inspector availability constraints
    for k, inspector in enumerate(inspectors):
        for i in range(1, n):
            model.addConstr(
                T[i, k] >= inspector.availability_start - BIGM * (1 - y[i, k]),
                name=f"avail_start_{i}_{k}"
            )
    
    # (10) Enforce max_work_hours constraint
    # Total work time (travel + service) must not exceed inspector's max work hours
    for k, inspector in enumerate(inspectors):
        if hasattr(inspector, 'max_work_hours') and inspector.max_work_hours is not None:
            total_work = gp.quicksum(
                dist[k][i][j] * x[i, j, k] 
                for i in range(n) for j in range(n)
            ) + gp.quicksum(
                tasks[i - 1].duration * y[i, k] 
                for i in range(1, n)
            )
            
            model.addConstr(
                total_work <= inspector.max_work_hours,
                name=f"max_work_hours_{k}"
            )
    
    # Optimize
    model.optimize()
    
    # Parse solution
    elapsed = time.time() - start_time
    
    if model.Status == GRB.INFEASIBLE:
        # Compute IIS (Irreducible Inconsistent Subsystem) to identify conflicting constraints
        print("\n" + "="*60)
        print("MODEL IS INFEASIBLE - Computing conflict diagnosis...")
        print("="*60)
        
        model.computeIIS()
        
        violated_constraints = []
        constraint_types = {}
        
        # Collect all constraints in IIS
        for constr in model.getConstrs():
            if constr.IISConstr:
                violated_constraints.append(constr.ConstrName)
                # Extract constraint type from name
                constr_type = constr.ConstrName.split('_')[0]
                if constr_type not in constraint_types:
                    constraint_types[constr_type] = []
                constraint_types[constr_type].append(constr.ConstrName)
        
        # Build detailed error message
        error_msg = "MODEL IS INFEASIBLE\n\n"
        error_msg += "VIOLATED CONSTRAINT TYPES:\n"
        error_msg += "-" * 60 + "\n"
        
        constraint_explanations = {
            "assign": "Task Assignment: Some tasks cannot be assigned to any inspector",
            "flow": "Flow Conservation: Route flow in/out doesn't balance",
            "depot": "Depot Rules: Inspector must start/end at depot",
            "skill": "Skill Matching: Inspector lacks required skill for task",
            "time": "Time Sequencing: Tasks cannot be completed in valid order",
            "tw": "Time Windows: Tasks cannot be done within their time windows",
            "avail": "Availability: Tasks scheduled outside inspector work hours",
            "no": "Self-loops: Invalid self-loop detected",
        }
        
        for constr_type, constraints in constraint_types.items():
            explanation = constraint_explanations.get(constr_type, f"Constraint type: {constr_type}")
            error_msg += f"\n• {explanation}\n"
            error_msg += f"  Violated: {len(constraints)} constraint(s)\n"
            if len(constraints) <= 5:
                for c in constraints:
                    error_msg += f"    - {c}\n"
            else:
                for c in constraints[:3]:
                    error_msg += f"    - {c}\n"
                error_msg += f"    ... and {len(constraints) - 3} more\n"
        
        error_msg += "\n" + "-" * 60 + "\n"
        error_msg += "POSSIBLE CAUSES:\n"
        error_msg += "• Inspector skills don't match required task skills\n"
        error_msg += "• Task time windows are too narrow or conflicting\n"
        error_msg += "• Inspector availability hours are insufficient\n"
        error_msg += "• Tasks are too far apart given time constraints\n"
        error_msg += "• Not enough inspectors to cover all tasks\n"
        
        print(error_msg)
        raise Exception(error_msg)
        
    elif model.Status == GRB.UNBOUNDED:
        raise Exception("Model is unbounded.")
    elif model.Status not in [GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL]:
        raise Exception(f"Gurobi failed with status {model.Status}")
    
    solver_status = "OPTIMAL" if model.Status == GRB.OPTIMAL else "TIME_LIMIT"
    
    # Extract routes
    routes_dict = {}
    total_travel = 0.0
    total_service = 0.0
    
    for k, inspector in enumerate(inspectors):
        route = []
        travel_time = 0.0
        service_time = 0.0
        tasks_done = 0
        
        # Reconstruct route by following arcs (using inspector-specific distances)
        current = depot_idx
        visited = set([current])
        
        while True:
            found_next = False
            for j in range(n):
                if x[current, j, k].X > 0.5 and j not in visited:
                    route.append(tasks[j - 1].id if j > 0 else 0)
                    travel_time += dist[k][current][j]  # Use inspector k's distance matrix
                    
                    if j > 0:
                        service_time += tasks[j - 1].duration
                        tasks_done += 1
                    
                    current = j
                    visited.add(j)
                    found_next = True
                    break
            
            if not found_next:
                # Try returning to inspector's starting location
                if current != depot_idx and x[current, depot_idx, k].X > 0.5:
                    travel_time += dist[k][current][depot_idx]  # Use inspector k's distance matrix
                    current = depot_idx
                    route.append(0)
                else:
                    break
        
        total_travel += travel_time
        total_service += service_time
        
        routes_dict[inspector.id] = RouteSolution(
            inspector_id=inspector.id,
            route=route,
            travel_time=travel_time,
            service_time=service_time,
            total_time=travel_time + service_time,
            tasks_completed=tasks_done,
        )
    
    gap = (model.MIPGap if hasattr(model, "MIPGap") else None)
    
    return SolutionResult(
        objective_value=model.ObjVal if model.SolCount > 0 else float("inf"),
        total_travel_time=total_travel,
        total_service_time=total_service,
        routes=routes_dict,
        solver_status=solver_status,
        solve_time=elapsed,
        gap=gap,
    )


# Export for backwards compatibility or standalone usage
if __name__ == "__main__":
    from dataset_generator import DatasetGenerator
    
    # Generate sample dataset
    inspectors, tasks, depot = DatasetGenerator.generate_dataset(
        num_inspectors=3,
        num_tasks=10,
        structured=True,
    )
    
    print("=" * 60)
    print("INSPECTION ROUTING OPTIMIZATION")
    print("=" * 60)
    print(f"\nDataset: {len(inspectors)} inspectors, {len(tasks)} tasks")
    print(f"Inspectors: {[i.id for i in inspectors]}")
    print(f"Tasks: {[t.id for t in tasks]}")
    
    # Solve
    solution = solve_routing(inspectors, tasks, depot, time_limit=30)
    
    print("\n" + "=" * 60)
    print("SOLUTION")
    print("=" * 60)
    print(solution.summary())
    
    print("\n" + "-" * 60)
    print("ROUTES BY INSPECTOR")
    print("-" * 60)
    for inspector_id, route_sol in solution.routes.items():
        print(f"\n{inspector_id}:")
        print(f"  Route: {route_sol.route}")
        print(f"  Travel Time: {route_sol.travel_time:.2f} h")
        print(f"  Service Time: {route_sol.service_time:.2f} h")
        print(f"  Total Time: {route_sol.total_time:.2f} h")
        print(f"  Tasks Completed: {route_sol.tasks_completed}")
