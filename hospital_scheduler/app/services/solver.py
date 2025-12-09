import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Employee, Shift, Demand, ScheduleRun, Assignment
from ..schemas import SolveRequest
import sys
import json

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
        
        # Weights for Multi-Objective
        self.W1_COST = 1.0
        self.W2_UNCOVERED = self.params.penalty_uncovered if self.params.penalty_uncovered else 1000.0
        self.W3_PREFERENCE = self.params.weight_preference  # Penalty for ignoring an "avoid" request

        # Internal State
        self.employees = []
        self.shifts = []
        self.dates = []
        self.demand_dict = {}
        self.all_skills = set()
        self.emp_map = {}
        self.shift_map = {}
        
        # Model & Variables
        self.model = None
        self.x = {} # Assignments
        self.y = {} # Slack/Uncovered

    def log(self, msg: str):
        print(f"[{self.run_id}] {msg}")
        self.log_buffer.append(f"{datetime.now().isoformat()} - {msg}")

    def solve(self):
        """
        Main execution flow for the Enterprise Scheduler.
        """
        run_record = self.db.query(ScheduleRun).filter(ScheduleRun.run_id == self.run_id).first()
        run_record.status = "PROCESSING"
        self.db.commit()

        try:
            self._fetch_data()
            self._build_model()
            self._build_variables()
            self._add_hard_constraints()
            self._add_soft_constraints()
            self._set_objective()
            self._optimize_and_save(run_record)

        except Exception as e:
            self.log(f"System Error: {e}")
            run_record.status = "ERROR"
            run_record.completed_at = datetime.utcnow()
            run_record.logs = "\n".join(self.log_buffer)
            self.db.commit()
            # Re-raise for debugging if needed, or swallow
            # raise e

    def _fetch_data(self):
        """
        Loads all necessary data from the database and prepares internal structures.
        """
        self.log("Fetching data...")
        self.employees = self.db.query(Employee).all()
        self.shifts = self.db.query(Shift).all()
        
        # Generate date range
        start_date = self.params.horizon_start
        self.dates = [start_date + timedelta(days=i) for i in range(self.params.horizon_days)]
        
        # Fetch Demand
        demand_rows = self.db.query(Demand).filter(
            Demand.date >= start_date,
            Demand.date < start_date + timedelta(days=self.params.horizon_days)
        ).all()
        
        # Mappings
        self.emp_map = {e.employee_id: e for e in self.employees}
        self.shift_map = {s.shift_id: s for s in self.shifts}
        
        # Demand Lookup: (date_str, shift_id, skill) -> count
        # Using date string for dictionary keys to avoid object identity issues
        self.demand_dict = {}
        self.all_skills = set()
        for r in demand_rows:
            d_str = r.date.strftime("%Y-%m-%d")
            self.demand_dict[(d_str, r.shift_id, r.skill)] = r.required
            self.all_skills.add(r.skill)
            
        self.log(f"Loaded {len(self.employees)} Employees, {len(self.shifts)} Shifts, {len(self.dates)} Days.")

    def _build_model(self):
        """Initialize Gurobi Model"""
        self.model = gp.Model(f"Hospital_Schedule_{self.run_id}")
        self.model.setParam("TimeLimit", self.params.solver_time_limit)
        self.model.setParam("LogToConsole", 0)

    def _build_variables(self):
        """
        Create decision variables.
        x[e, t, s]: Binary, 1 if employee e works shift s on day t.
        y[t, s, u]: Integer, amount of uncovered demand for skill u on shift s, day t.
        """
        self.log("Building variables...")
        
        # 1. Assignment Variables (x)
        for e in self.employees:
            for t in self.dates:
                t_str = t.strftime("%Y-%m-%d")
                for s in self.shifts:
                    # Check basic availability (if defined in JSON)
                    # Assuming availability JSON structure: {"2025-01-01": ["unavail", "morning"]}
                    # If "unavail" is present for the day, skip creating variable (Hard unavailability)
                    is_available = True
                    if e.availability:
                        day_avail = e.availability.get(t_str, [])
                        if "unavailable" in day_avail:
                            is_available = False
                    
                    if is_available:
                        self.x[(e.employee_id, t_str, s.shift_id)] = self.model.addVar(
                            vtype=GRB.BINARY, 
                            name=f"x_{e.employee_id}_{t_str}_{s.shift_id}"
                        )

        # 2. Elastic Demand Variables (y) - Always created for robustness
        for t in self.dates:
            t_str = t.strftime("%Y-%m-%d")
            for s in self.shifts:
                for u in self.all_skills:
                    self.y[(t_str, s.shift_id, u)] = self.model.addVar(
                        lb=0, 
                        vtype=GRB.CONTINUOUS, # Can be integer, but continuous is often fine for slack
                        name=f"y_{t_str}_{s.shift_id}_{u}"
                    )
        
        self.model.update()

    def _add_hard_constraints(self):
        """
        Add operational constraints that MUST be satisfied (or use slack variables).
        """
        self.log("Adding hard constraints...")
        m = self.model
        
        # C1: Coverage Demand (Elastic)
        # Sum(workers with skill U) + Uncovered_Slack >= Required
        for t in self.dates:
            t_str = t.strftime("%Y-%m-%d")
            for s in self.shifts:
                for u in self.all_skills:
                    req = self.demand_dict.get((t_str, s.shift_id, u), 0)
                    if req > 0:
                        workers = []
                        for e in self.employees:
                            # Check if variable exists (availability check)
                            if (e.employee_id, t_str, s.shift_id) in self.x:
                                # Check if employee has the skill
                                if u in e.skills.split("|"):
                                    workers.append(self.x[(e.employee_id, t_str, s.shift_id)])
                        
                        # Elastic constraint: Workers + Slack >= Demand
                        m.addConstr(gp.quicksum(workers) + self.y[(t_str, s.shift_id, u)] >= req, 
                                    name=f"cov_{t_str}_{s.shift_id}_{u}")

        # C2: One Shift Per Day
        for e in self.employees:
            for t in self.dates:
                t_str = t.strftime("%Y-%m-%d")
                daily_shifts = [self.x[(e.employee_id, t_str, s.shift_id)] 
                                for s in self.shifts 
                                if (e.employee_id, t_str, s.shift_id) in self.x]
                if daily_shifts:
                    m.addConstr(gp.quicksum(daily_shifts) <= 1, name=f"one_shift_{e.employee_id}_{t_str}")

        # C3: Max Hours Per Horizon
        for e in self.employees:
            total_hours = gp.quicksum(
                self.x[(e.employee_id, t.strftime("%Y-%m-%d"), s.shift_id)] * s.length_hours
                for t in self.dates
                for s in self.shifts
                if (e.employee_id, t.strftime("%Y-%m-%d"), s.shift_id) in self.x
            )
            m.addConstr(total_hours <= e.max_weekly_hours, name=f"max_hours_{e.employee_id}")

            # C4: Minimum Rest Time (11h rule) & Forward Rotation
        # We iterate adjacent days.
        # Forbidden: Shift A (Day T) -> Shift B (Day T+1) if gap < min_rest
        # ALSO Forbidden: Night -> Morning (Forward Rotation Rule)
        
        # Precompute forbidden pairs (s1, s2)
        min_rest = self.params.min_rest_hours
        forbidden_pairs = set()
        for s1 in self.shifts:
            for s2 in self.shifts:
                # 1. Calculate gap
                t1_end = int(s1.end_time.split(":")[0])
                t2_start = int(s2.start_time.split(":")[0])
                
                # Adjust for night shifts crossing midnight
                if s1.shift_type.lower() == "night" and t1_end < 12:
                    t1_end += 24
                
                gap = (24 - t1_end) + t2_start
                
                if gap < min_rest:
                    forbidden_pairs.add((s1.shift_id, s2.shift_id))                # 2. Forward Rotation Rule: Night -> Morning is forbidden
                # Even if gap >= 11 (e.g. Night ends 7am, Morning starts 7pm? Unlikely but logic holds)
                # Usually Night ends 7am, Morning starts 7am next day -> 24h gap. 
                # But "Night -> Morning" usually means Night (Day T) -> Morning (Day T+1).
                # If Night ends 07:00, Morning starts 07:00, gap is 0. Already covered by 11h rule?
                # Let's assume Morning starts 06:00 or 07:00.
                # If Night ends 07:00, gap is 0.
                # If Night ends 23:00, Morning starts 07:00, gap is 8.
                # Explicitly adding it ensures business logic compliance regardless of times.
                if s1.shift_type.lower() == "night" and s2.shift_type.lower() == "morning":
                    forbidden_pairs.add((s1.shift_id, s2.shift_id))

        for e in self.employees:
            for i in range(len(self.dates) - 1):
                t_curr = self.dates[i].strftime("%Y-%m-%d")
                t_next = self.dates[i+1].strftime("%Y-%m-%d")
                
                for (s1_id, s2_id) in forbidden_pairs:
                    # If both variables exist
                    if (e.employee_id, t_curr, s1_id) in self.x and \
                       (e.employee_id, t_next, s2_id) in self.x:
                        m.addConstr(
                            self.x[(e.employee_id, t_curr, s1_id)] + 
                            self.x[(e.employee_id, t_next, s2_id)] <= 1,
                            name=f"rest_rot_{e.employee_id}_{t_curr}"
                        )

        # C5: Max Consecutive Working Days (e.g., 5)
        MAX_CONSECUTIVE = self.params.max_consecutive_days
        for e in self.employees:
            # Sliding window of size MAX_CONSECUTIVE + 1
            # Sum of working days in window <= MAX_CONSECUTIVE
            for i in range(len(self.dates) - MAX_CONSECUTIVE):
                window_days = self.dates[i : i + MAX_CONSECUTIVE + 1]
                
                # Expression: Sum(Any shift on day t for t in window)
                # Let d_t = Sum(x[e,t,s]) for all s. d_t is binary (0 or 1) due to C2 (One shift per day)
                # Constraint: Sum(d_t) <= MAX_CONSECUTIVE
                
                window_expr = 0
                for t in window_days:
                    t_str = t.strftime("%Y-%m-%d")
                    for s in self.shifts:
                        if (e.employee_id, t_str, s.shift_id) in self.x:
                            window_expr += self.x[(e.employee_id, t_str, s.shift_id)]
                
                m.addConstr(window_expr <= MAX_CONSECUTIVE, name=f"max_consec_{e.employee_id}_{i}")

        # C6: Ratio Constraints (ICU Rule)
        # "For every 1 Junior, at least 1 Senior" -> Senior_Count >= Junior_Count
        # Only applies if shift name contains "ICU" (or similar logic)
        # We assume skills contain "Senior" or "Junior"
        icu_shifts = [s for s in self.shifts if "ICU" in s.name.upper() or "ICU" in s.shift_id.upper()]
        
        if icu_shifts:
            for t in self.dates:
                t_str = t.strftime("%Y-%m-%d")
                for s in icu_shifts:
                    seniors = []
                    juniors = []
                    
                    for e in self.employees:
                        if (e.employee_id, t_str, s.shift_id) in self.x:
                            skills = e.skills.upper().split("|")
                            if "SENIOR" in skills:
                                seniors.append(self.x[(e.employee_id, t_str, s.shift_id)])
                            elif "JUNIOR" in skills:
                                juniors.append(self.x[(e.employee_id, t_str, s.shift_id)])
                    
                    # Constraint: Sum(Seniors) >= Sum(Juniors)
                    if seniors or juniors:
                        m.addConstr(gp.quicksum(seniors) >= gp.quicksum(juniors), 
                                    name=f"ratio_icu_{t_str}_{s.shift_id}")

        # C7: Max Night Shifts per Employee
        # Sum(Night Shifts) <= MAX_NIGHTS
        MAX_NIGHTS = self.params.max_night_shifts
        night_shifts = [s for s in self.shifts if s.shift_type.lower() == "night"]
        
        if night_shifts:
            for e in self.employees:
                night_vars = []
                for t in self.dates:
                    t_str = t.strftime("%Y-%m-%d")
                    for s in night_shifts:
                        if (e.employee_id, t_str, s.shift_id) in self.x:
                            night_vars.append(self.x[(e.employee_id, t_str, s.shift_id)])
                
                if night_vars:
                    m.addConstr(gp.quicksum(night_vars) <= MAX_NIGHTS, 
                                name=f"max_nights_{e.employee_id}")

        # C8: Minimum Shifts per Employee (Fairness)
        MIN_SHIFTS = self.params.min_shifts_per_employee
        if MIN_SHIFTS > 0:
            for e in self.employees:
                total_shifts = []
                for t in self.dates:
                    t_str = t.strftime("%Y-%m-%d")
                    for s in self.shifts:
                        if (e.employee_id, t_str, s.shift_id) in self.x:
                            total_shifts.append(self.x[(e.employee_id, t_str, s.shift_id)])
                
                if total_shifts:
                    m.addConstr(gp.quicksum(total_shifts) >= MIN_SHIFTS, 
                                name=f"min_shifts_{e.employee_id}")

        # C9: Complete Weekends (If working Sat, must work Sun)
        if self.params.require_complete_weekends:
            for t in self.dates:
                if t.weekday() == 5: # Saturday
                    t_sat_str = t.strftime("%Y-%m-%d")
                    t_sun = t + timedelta(days=1)
                    t_sun_str = t_sun.strftime("%Y-%m-%d")
                    
                    # Only enforce if Sunday is also in the horizon
                    if t_sun in self.dates:
                        for e in self.employees:
                            sat_vars = []
                            sun_vars = []
                            
                            for s in self.shifts:
                                if (e.employee_id, t_sat_str, s.shift_id) in self.x:
                                    sat_vars.append(self.x[(e.employee_id, t_sat_str, s.shift_id)])
                                if (e.employee_id, t_sun_str, s.shift_id) in self.x:
                                    sun_vars.append(self.x[(e.employee_id, t_sun_str, s.shift_id)])
                            
                            # Sum(Sat) == Sum(Sun). Since max 1 shift/day, this means 0==0 or 1==1
                            if sat_vars and sun_vars:
                                m.addConstr(gp.quicksum(sat_vars) == gp.quicksum(sun_vars),
                                            name=f"complete_weekend_{e.employee_id}_{t_sat_str}")

    def _add_soft_constraints(self):
        """
        Add soft constraints (Preferences) by adding terms to the objective function later,
        or tracking violations with variables if needed. 
        Here we'll prepare the penalty terms for the objective.
        """
        self.log("Adding soft constraints (Preferences)...")
        # We will handle this in _set_objective by iterating preferences
        pass

    def _set_objective(self):
        """
        Construct the Multi-Objective Function:
        Minimize Z = (W1 * Cost) + (W2 * Uncovered) + (W3 * Preferences)
        """
        self.log("Setting objective function...")
        
        # 1. Labor Cost
        cost_expr = 0
        for (e_id, t_str, s_id), var in self.x.items():
            emp = self.emp_map[e_id]
            shift = self.shift_map[s_id]
            cost_expr += var * emp.hourly_cost * shift.length_hours

        # 2. Uncovered Demand Penalty
        uncovered_expr = 0
        for var in self.y.values():
            uncovered_expr += var # Sum of hours/people missing

        # 3. Preference Violations
        # Check employee availability/preferences for "avoid"
        pref_expr = 0
        for e in self.employees:
            if not e.availability:
                continue
            
            for t_str, prefs in e.availability.items():
                # prefs might be ["avoid_night", "prefer_morning"] or simple list
                # Let's assume structure: { "2025-12-01": ["avoid_S3", "avoid_night"] }
                for pref in prefs:
                    if pref.startswith("avoid_"):
                        target = pref.replace("avoid_", "") # e.g. "S3" or "night"
                        
                        # Find matching variables
                        for s in self.shifts:
                            # Match by Shift ID or Shift Type
                            if s.shift_id == target or s.shift_type == target:
                                if (e.employee_id, t_str, s.shift_id) in self.x:
                                    # If assigned, add penalty
                                    pref_expr += self.x[(e.employee_id, t_str, s.shift_id)]

        # Combine
        total_obj = (self.W1_COST * cost_expr) + \
                    (self.W2_UNCOVERED * uncovered_expr) + \
                    (self.W3_PREFERENCE * pref_expr)
        
        self.model.setObjective(total_obj, GRB.MINIMIZE)

    def _optimize_and_save(self, run_record: ScheduleRun):
        """
        Run solver, handle infeasibility, and save results.
        """
        self.log("Starting Optimization...")
        self.model.optimize()
        
        status = self.model.Status
        
        if status == GRB.OPTIMAL or status == GRB.TIME_LIMIT:
            if self.model.SolCount > 0:
                self._save_solution(run_record, status)
            else:
                run_record.status = "NO_SOLUTION"
                self.log("Time limit reached, no solution found.")
        
        elif status == GRB.INFEASIBLE:
            self.log("Model is INFEASIBLE. Computing IIS...")
            run_record.status = "INFEASIBLE"
            
            # Compute IIS to find conflicting constraints
            try:
                self.model.computeIIS()
                self.model.write(f"model_{self.run_id}.ilp")
                
                self.log("IIS Computed. Conflicting constraints:")
                for c in self.model.getConstrs():
                    if c.IISConstr:
                        self.log(f" - {c.ConstrName}")
            except Exception as e:
                self.log(f"Failed to compute IIS: {e}")
                
        else:
            run_record.status = f"ERROR_{status}"
            self.log(f"Solver finished with status {status}")

        run_record.logs = "\n".join(self.log_buffer)
        run_record.completed_at = datetime.utcnow()
        self.db.commit()

    def _save_solution(self, run_record: ScheduleRun, status_code):
        run_record.status = "OPTIMAL" if status_code == GRB.OPTIMAL else "FEASIBLE"
        run_record.objective_value = self.model.ObjVal
        
        assignments = []
        for (e_id, t_str, s_id), var in self.x.items():
            if var.X > 0.5:
                s_obj = self.shift_map[s_id]
                e_obj = self.emp_map[e_id]
                cost = e_obj.hourly_cost * s_obj.length_hours
                
                assignments.append(Assignment(
                    run_id=self.run_id,
                    employee_id=e_id,
                    date=datetime.strptime(t_str, "%Y-%m-%d").date(),
                    shift_id=s_id,
                    hours=s_obj.length_hours,
                    cost=cost,
                    is_overtime=False
                ))
        
        self.db.add_all(assignments)
        self.log(f"Solution saved: {len(assignments)} assignments.")

