from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid

from ...database import get_db, SessionLocal
from ...models import ScheduleRun, Employee, Shift
from ...schemas import SolveRequest, RunResponse, RunStatusResponse, RunSummarySchema, AssignmentSchema
from ...services.solver import GurobiScheduler

router = APIRouter(
    prefix="/schedules",
    tags=["schedules"]
)

# Background Task Wrapper
def run_solver_task(run_id: str, params: SolveRequest):
    # Create a new DB session for the background thread
    db = SessionLocal()
    try:
        scheduler = GurobiScheduler(db, run_id, params)
        scheduler.solve()
    finally:
        db.close()

@router.post("/", response_model=RunResponse)
def create_schedule(request: SolveRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Submit a request to generate a schedule.
    """
    run_id = str(uuid.uuid4())
    
    # Create Run Record
    new_run = ScheduleRun(
        run_id=run_id,
        status="QUEUED",
        horizon_start=request.horizon_start,
        horizon_days=request.horizon_days,
        solver_params=request.model_dump(mode='json')
    )
    db.add(new_run)
    db.commit()
    
    # Enqueue Task
    background_tasks.add_task(run_solver_task, run_id, request)
    
    return RunResponse(run_id=run_id, status="QUEUED", message="Job submitted successfully.")

@router.get("/", response_model=List[RunSummarySchema])
def list_schedules(db: Session = Depends(get_db)):
    """
    Get a list of all schedule runs, ordered by creation date (newest first).
    """
    runs = db.query(ScheduleRun).order_by(ScheduleRun.created_at.desc()).all()
    
    summaries = []
    for run in runs:
        summaries.append(RunSummarySchema(
            run_id=run.run_id,
            status=run.status,
            objective_value=run.objective_value,
            created_at=run.created_at,
            completed_at=run.completed_at,
            assignment_count=len(run.assignments) if run.assignments else 0
        ))
    
    return summaries

@router.get("/{run_id}", response_model=RunStatusResponse)
def get_schedule_status(run_id: str, db: Session = Depends(get_db)):
    """
    Poll the status of a run and get results if finished.
    """
    run = db.query(ScheduleRun).filter(ScheduleRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    assign_schemas = []
    if run.status in ["OPTIMAL", "FEASIBLE"]:
        # Pre-load data for enrichment
        emp_map = {}
        shift_map = {}
        
        for a in run.assignments:
            # Get employee info if not cached
            if a.employee_id not in emp_map:
                emp = db.query(Employee).filter(Employee.employee_id == a.employee_id).first()
                if emp:
                    emp_map[a.employee_id] = emp
            
            # Get shift info if not cached
            if a.shift_id not in shift_map:
                shift = db.query(Shift).filter(Shift.shift_id == a.shift_id).first()
                if shift:
                    shift_map[a.shift_id] = shift
            
            # Build enriched assignment
            emp_obj = emp_map.get(a.employee_id)
            shift_obj = shift_map.get(a.shift_id)
            
            assign_schemas.append(AssignmentSchema(
                employee_id=a.employee_id,
                employee_name=emp_obj.name if emp_obj else a.employee_id,
                role=emp_obj.role if emp_obj else "Unknown",
                date=a.date,
                shift_id=a.shift_id,
                shift_name=shift_obj.name if shift_obj else a.shift_id,
                hours=a.hours,
                cost=a.cost
            ))
            
    return RunStatusResponse(
        run_id=run.run_id,
        status=run.status,
        objective_value=run.objective_value,
        logs=run.logs,
        assignments=assign_schemas,
        created_at=run.created_at,
        completed_at=run.completed_at
    )
