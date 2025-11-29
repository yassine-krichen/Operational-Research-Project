from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models import Shift as ShiftModel
from ...schemas import Shift, ShiftCreate

router = APIRouter(
    prefix="/shifts",
    tags=["shifts"]
)

@router.get("/", response_model=List[Shift])
def read_shifts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    shifts = db.query(ShiftModel).offset(skip).limit(limit).all()
    return shifts

@router.post("/", response_model=Shift)
def create_shift(shift: ShiftCreate, db: Session = Depends(get_db)):
    db_shift = db.query(ShiftModel).filter(ShiftModel.shift_id == shift.shift_id).first()
    if db_shift:
        raise HTTPException(status_code=400, detail="Shift ID already exists")
    
    new_shift = ShiftModel(
        shift_id=shift.shift_id,
        name=shift.name,
        start_time=shift.start_time,
        end_time=shift.end_time,
        length_hours=shift.length_hours,
        shift_type=shift.shift_type
    )
    db.add(new_shift)
    db.commit()
    db.refresh(new_shift)
    return new_shift

@router.get("/{shift_id}", response_model=Shift)
def read_shift(shift_id: str, db: Session = Depends(get_db)):
    db_shift = db.query(ShiftModel).filter(ShiftModel.shift_id == shift_id).first()
    if db_shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    return db_shift

@router.delete("/{shift_id}")
def delete_shift(shift_id: str, db: Session = Depends(get_db)):
    db_shift = db.query(ShiftModel).filter(ShiftModel.shift_id == shift_id).first()
    if db_shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    db.delete(db_shift)
    db.commit()
    return {"message": "Shift deleted successfully"}
