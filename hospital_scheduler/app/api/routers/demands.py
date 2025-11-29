from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from ...database import get_db
from ...models import Demand as DemandModel
from ...schemas import Demand, DemandCreate

router = APIRouter(
    prefix="/demands",
    tags=["demands"]
)

@router.get("/", response_model=List[Demand])
def read_demands(start_date: date = None, end_date: date = None, db: Session = Depends(get_db)):
    query = db.query(DemandModel)
    if start_date:
        query = query.filter(DemandModel.date >= start_date)
    if end_date:
        query = query.filter(DemandModel.date <= end_date)
    return query.all()

@router.post("/", response_model=Demand)
def create_demand(demand: DemandCreate, db: Session = Depends(get_db)):
    new_demand = DemandModel(
        date=demand.date,
        shift_id=demand.shift_id,
        skill=demand.skill,
        required=demand.required
    )
    db.add(new_demand)
    db.commit()
    db.refresh(new_demand)
    return new_demand

@router.delete("/{demand_id}")
def delete_demand(demand_id: int, db: Session = Depends(get_db)):
    db_demand = db.query(DemandModel).filter(DemandModel.id == demand_id).first()
    if db_demand is None:
        raise HTTPException(status_code=404, detail="Demand not found")
    db.delete(db_demand)
    db.commit()
    return {"message": "Demand deleted successfully"}
