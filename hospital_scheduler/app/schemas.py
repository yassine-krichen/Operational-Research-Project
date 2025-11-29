from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional, Dict, Any

# --- Employee Schemas ---
class EmployeeBase(BaseModel):
    name: str
    role: str
    skills: str
    hourly_cost: float
    max_weekly_hours: float = 40.0
    min_weekly_hours: float = 0.0
    availability: Optional[Dict[str, Any]] = None

class EmployeeCreate(EmployeeBase):
    employee_id: str

class Employee(EmployeeBase):
    employee_id: str
    
    class Config:
        from_attributes = True

# --- Shift Schemas ---
class ShiftBase(BaseModel):
    name: str
    start_time: str
    end_time: str
    length_hours: float
    shift_type: str

class ShiftCreate(ShiftBase):
    shift_id: str

class Shift(ShiftBase):
    shift_id: str

    class Config:
        from_attributes = True

# --- Demand Schemas ---
class DemandBase(BaseModel):
    date: date
    shift_id: str
    skill: str
    required: int

class DemandCreate(DemandBase):
    pass

class Demand(DemandBase):
    id: int

    class Config:
        from_attributes = True

# --- Solver Schemas ---
class SolveRequest(BaseModel):
    horizon_start: date
    horizon_days: int = 7
    solver_time_limit: int = 60
    allow_uncovered_demand: bool = True
    penalty_uncovered: float = 1000.0
    weight_preference: float = 50.0
    max_consecutive_days: int = 5

class RunResponse(BaseModel):
    run_id: str
    status: str
    message: str

class AssignmentSchema(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    date: date
    shift_id: str
    shift_name: str
    hours: float
    cost: float

class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    objective_value: Optional[float] = None
    logs: Optional[str] = None
    assignments: List[AssignmentSchema] = []
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class RunSummarySchema(BaseModel):
    """Summary of a schedule run for list display"""
    run_id: str
    status: str
    objective_value: Optional[float] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assignment_count: int = 0
