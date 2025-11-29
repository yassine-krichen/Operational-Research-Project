import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Employee, Shift, Demand, ScheduleRun, Assignment
from ..schemas import SolveRequest
import sys

# Check for Gurobi
try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:
    print("CRITICAL: gurobipy is not installed. Please install it via 'pip install gurobipy'.")
    sys.exit(1)

class GurobiScheduler:
    def __init__(self, db: Session, run_id: str, params: SolveRequest):
        self.db = db
        self.run_id = run_id
        self.params = params
        self.log_buffer = []
    
    def log(self, msg: str):
        print(f"[{self.run_id}] {msg}")
        self.log_buffer.append(f"{datetime.now().isoformat()} - {msg}")

    def solve(self):
        run_record = self.db.query(ScheduleRun).filter(ScheduleRun.run_id == self.run_id).first()
        run_record.status = "PROCESSING"
        self.db.commit()

        try:
            # 1. Fetch Data
            employees = self.db.query(Employee).all()
            shifts = self.db.query(Shift).all()
            
            # Generate date range
            start_date = self.params.horizon_start
            dates = [start_date + timedelta(days=i) for i in range(self.params.horizon_days)]
            
            # Fetch Demand for this horizon
            demand_rows = self.db.query(Demand).filter(
                Demand.date >= start_date,
                Demand.date < start_date + timedelta(days=self.params.horizon_days)
            ).all()
            
            # Organize Data
            E = [e.employee_id for e in employees]
            S = [s.shift_id for s in shifts]
            T = dates
            
            # Mappings
            emp_map = {e.employee_id: e for e in employees}
            shift_map = {s.shift_id: s for s in shifts}
            
            # Demand Lookup: (date, shift_id, skill) -> count
            demand_dict = {}
            all_skills = set()
            for r in demand_rows:
                demand_dict[(r.date, r.shift_id, r.skill)] = r.required
                all_skills.add(r.skill)
            
            # 2. Build Model
            m = gp.Model(f"Hospital_Schedule_{self.run_id}")
            m.setParam("TimeLimit", self.params.solver_time_limit)
            m.setParam("LogToConsole", 0) # Handle logs manually via callbacks or extraction if needed
            
            self.log(f"Building model: {len(E)} Employees, {len(T)} Days, {len(S)} Shifts")

            # --- Variables ---
            # x[e, t, s] = 1 if employee e works shift s on day t
            x = {}
            possible_assignments = 0
            
            for e_id in E:
                emp = emp_map[e_id]
                emp_skills = emp.skills.split("|")
                
                # Check explicit availability if JSON is present
                avail_rules = emp.availability if emp.availability else {}
                
                for t in T:
                    day_str = t.strftime("%Y-%m-%d")
                    day_of_week = t.strftime("%a").lower() # mon, tue...
                    
                    # Basic availability filter could go here
                    
                    for s_id in S:
                        x[(e_id, t, s_id)] = m.addVar(vtype=GRB.BINARY, name=f"x_{e_id}_{t}_{s_id}")
                        possible_assignments += 1

            # y[t, s, u] = uncovered demand (slack)
            y = {}
            if self.params.allow_uncovered_demand:
                for t in T:
                    for s_id in S:
                        for u in all_skills:
                            y[(t, s_id, u)] = m.addVar(lb=0, name=f"y_{t}_{s_id}_{u}")

            m.update()
            
            # --- Constraints ---

            # C1: Coverage Demand
            # Sum(employees working shift S on day T having skill U) >= Demand - Slack
            for t in T:
                for s_id in S:
                    for u in all_skills:
                        req = demand_dict.get((t, s_id, u), 0)
                        if req > 0:
                            workers_covering = []
                            for e_id in E:
                                emp = emp_map[e_id]
                                if u in emp.skills.split("|"): # Check if employee has skill
                                    workers_covering.append(x[(e_id, t, s_id)])
                            
                            if self.params.allow_uncovered_demand:
                                m.addConstr(gp.quicksum(workers_covering) + y[(t, s_id, u)] >= req, name=f"cov_{t}_{s_id}_{u}")
                            else:
                                m.addConstr(gp.quicksum(workers_covering) >= req, name=f"cov_{t}_{s_id}_{u}")

            # C2: One Shift Per Day
            for e_id in E:
                for t in T:
                    m.addConstr(gp.quicksum(x[(e_id, t, s_id)] for s_id in S) <= 1, name=f"one_shift_{e_id}_{t}")

            # C3: Max Hours Per Horizon
            for e_id in E:
                emp = emp_map[e_id]
                total_hours_expr = gp.quicksum(
                    x[(e_id, t, s_id)] * shift_map[s_id].length_hours 
                    for t in T for s_id in S
                )
                m.addConstr(total_hours_expr <= emp.max_weekly_hours, name=f"max_hours_{e_id}")

            # C4: Minimum Rest Time (Forbidden Sequences)
            # 11 hours rest required. 
            # If Shift A ends at 23:00 (Day T) and Shift B starts at 07:00 (Day T+1), gap is 8h. Forbidden.
            # We iterate all adjacent day pairs (t, t+1) and shift pairs (s1, s2).
            min_rest = 11.0
            
            # Precompute forbidden pairs
            forbidden_pairs = []
            for s1_id in S:
                for s2_id in S:
                    s1 = shift_map[s1_id]
                    s2 = shift_map[s2_id]
                    
                    # Parse times (simplified)
                    # Assume simple day boundaries for this demo.
                    # Complex logic requires full datetime parsing of shift definitions
                    t1_end = int(s1.end_time.split(":")[0])
                    t2_start = int(s2.start_time.split(":")[0])
                    
                    # Adjust for shifts ending next day (like night shift)
                    # This is a simplified heuristic for the demo
                    if s1.shift_type == "night" and t1_end < 12: 
                        t1_end += 24 # Logically extends past midnight

                    gap = (24 - t1_end) + t2_start
                    if gap < min_rest:
                        forbidden_pairs.append((s1_id, s2_id))

            for e_id in E:
                for i in range(len(T) - 1):
                    t_curr = T[i]
                    t_next = T[i+1]
                    for (s1, s2) in forbidden_pairs:
                        m.addConstr(x[(e_id, t_curr, s1)] + x[(e_id, t_next, s2)] <= 1, 
                                    name=f"rest_{e_id}_{t_curr}")

            # --- Objective ---
            # Minimize (Labor Cost + Uncovered Penalties)
            cost_expr = 0
            for e_id in E:
                emp = emp_map[e_id]
                for t in T:
                    for s_id in S:
                        s = shift_map[s_id]
                        cost_expr += x[(e_id, t, s_id)] * emp.hourly_cost * s.length_hours
            
            penalty_expr = 0
            if self.params.allow_uncovered_demand:
                for key in y:
                    penalty_expr += y[key] * self.params.penalty_uncovered

            m.setObjective(cost_expr + penalty_expr, GRB.MINIMIZE)

            # 3. Solve
            self.log("Starting Optimization...")
            m.optimize()

            # 4. Process Results
            status_code = m.Status
            run_record.logs = "\n".join(self.log_buffer)
            
            if status_code == GRB.OPTIMAL or status_code == GRB.TIME_LIMIT:
                if m.SolCount > 0:
                    run_record.status = "OPTIMAL" if status_code == GRB.OPTIMAL else "FEASIBLE"
                    run_record.objective_value = m.ObjVal
                    
                    assignments = []
                    for (e_id, t, s_id), var in x.items():
                        if var.X > 0.5:
                            s_obj = shift_map[s_id]
                            e_obj = emp_map[e_id]
                            cost = e_obj.hourly_cost * s_obj.length_hours
                            
                            assignments.append(Assignment(
                                run_id=self.run_id,
                                employee_id=e_id,
                                date=t,
                                shift_id=s_id,
                                hours=s_obj.length_hours,
                                cost=cost,
                                is_overtime=False # Simplified logic
                            ))
                    
                    self.db.add_all(assignments)
                    self.log(f"Solution found: {len(assignments)} assignments.")
                else:
                    run_record.status = "NO_SOLUTION"
                    self.log("Time limit reached, no integer solution found.")
            elif status_code == GRB.INFEASIBLE:
                run_record.status = "INFEASIBLE"
                self.log("Model is infeasible.")
                # m.computeIIS() # Optional: write .ilp file for debug
            else:
                run_record.status = f"ERROR_{status_code}"
            
            # Set completion timestamp
            run_record.completed_at = datetime.utcnow()
            self.db.commit()

        except gp.GurobiError as e:
            self.log(f"Gurobi Error: {e}")
            run_record.status = "ERROR"
            run_record.completed_at = datetime.utcnow()
            run_record.logs = "\n".join(self.log_buffer)
            self.db.commit()
        except Exception as e:
            self.log(f"System Error: {e}")
            run_record.status = "ERROR"
            run_record.completed_at = datetime.utcnow()
            run_record.logs = "\n".join(self.log_buffer)
            self.db.commit()
