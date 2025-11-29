from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Employee(Base):
    __tablename__ = "employees"
    employee_id = Column(String, primary_key=True)
    name = Column(String)
    role = Column(String)
    skills = Column(String)  # Pipe separated "RN|ICU"
    hourly_cost = Column(Float)
    max_weekly_hours = Column(Float, default=40.0)
    min_weekly_hours = Column(Float, default=0.0)
    availability = Column(JSON)  # {"2025-12-01": ["morning"], ...}

class Shift(Base):
    __tablename__ = "shifts"
    shift_id = Column(String, primary_key=True)
    name = Column(String)
    start_time = Column(String) # HH:MM
    end_time = Column(String)   # HH:MM
    length_hours = Column(Float)
    shift_type = Column(String) # day/night

class Demand(Base):
    __tablename__ = "demand"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    shift_id = Column(String, ForeignKey("shifts.shift_id"))
    skill = Column(String)
    required = Column(Integer)

class ScheduleRun(Base):
    __tablename__ = "runs"
    run_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String) # QUEUED, PROCESSING, OPTIMAL, INFEASIBLE, ERROR
    horizon_start = Column(Date)
    horizon_days = Column(Integer)
    objective_value = Column(Float, nullable=True)
    solver_params = Column(JSON)
    logs = Column(String, nullable=True)

    assignments = relationship("Assignment", back_populates="run")

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.run_id"))
    employee_id = Column(String)
    date = Column(Date)
    shift_id = Column(String)
    hours = Column(Float)
    cost = Column(Float)
    is_overtime = Column(Boolean, default=False)
    
    run = relationship("ScheduleRun", back_populates="assignments")
