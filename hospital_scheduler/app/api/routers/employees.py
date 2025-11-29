from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models import Employee as EmployeeModel
from ...schemas import Employee, EmployeeCreate

router = APIRouter(
    prefix="/employees",
    tags=["employees"]
)

@router.get("/", response_model=List[Employee])
def read_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    employees = db.query(EmployeeModel).offset(skip).limit(limit).all()
    return employees

@router.post("/", response_model=Employee)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = db.query(EmployeeModel).filter(EmployeeModel.employee_id == employee.employee_id).first()
    if db_employee:
        raise HTTPException(status_code=400, detail="Employee already registered")
    
    new_employee = EmployeeModel(
        employee_id=employee.employee_id,
        name=employee.name,
        role=employee.role,
        skills=employee.skills,
        hourly_cost=employee.hourly_cost,
        max_weekly_hours=employee.max_weekly_hours,
        min_weekly_hours=employee.min_weekly_hours,
        availability=employee.availability
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return new_employee

@router.get("/{employee_id}", response_model=Employee)
def read_employee(employee_id: str, db: Session = Depends(get_db)):
    db_employee = db.query(EmployeeModel).filter(EmployeeModel.employee_id == employee_id).first()
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@router.delete("/{employee_id}")
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    db_employee = db.query(EmployeeModel).filter(EmployeeModel.employee_id == employee_id).first()
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(db_employee)
    db.commit()
    return {"message": "Employee deleted successfully"}
