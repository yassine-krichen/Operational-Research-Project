from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class SolveRequest(BaseModel):
    horizon_start: date
    horizon_days: int = 7
    solver_time_limit: int = 60
    allow_uncovered_demand: bool = True
    penalty_uncovered: float = 1000.0

class RunResponse(BaseModel):
    run_id: str
    status: str
    message: str

class AssignmentSchema(BaseModel):
    employee_id: str
    date: date
    shift_id: str
    hours: float
    cost: float

class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    objective: Optional[float]
    logs: Optional[str]
    assignments: List[AssignmentSchema] = []
