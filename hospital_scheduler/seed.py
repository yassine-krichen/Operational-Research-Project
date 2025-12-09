from sqlalchemy.orm import Session
try:
    from hospital_scheduler.app.models import Employee, Shift, Demand, Assignment, ScheduleRun
    from hospital_scheduler.app.database import SessionLocal, engine, Base
except ImportError:
    from app.models import Employee, Shift, Demand, Assignment, ScheduleRun
    from app.database import SessionLocal, engine, Base
from datetime import date, timedelta

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Assignment).delete()
        db.query(Demand).delete()
        db.query(Shift).delete()
        db.query(Employee).delete()
        db.query(ScheduleRun).delete()
        
        # 1. Shifts
        shifts = [
            Shift(shift_id="S1", name="Morning", start_time="07:00", end_time="15:00", length_hours=8, shift_type="day"),
            Shift(shift_id="S2", name="Afternoon", start_time="15:00", end_time="23:00", length_hours=8, shift_type="day"),
            Shift(shift_id="S3", name="Night", start_time="23:00", end_time="07:00", length_hours=8, shift_type="night"),
        ]
        db.add_all(shifts)
        
        # 2. Employees
        employees = [
            Employee(employee_id="E01", name="Alice", role="Nurse", skills="RN", hourly_cost=30.0, max_weekly_hours=40),
            Employee(employee_id="E02", name="Bob", role="Nurse", skills="RN|ICU", hourly_cost=45.0, max_weekly_hours=40),
            Employee(employee_id="E03", name="Charlie", role="Nurse", skills="RN", hourly_cost=32.0, max_weekly_hours=20),
            Employee(employee_id="D01", name="Dr. Smith", role="Doctor", skills="MD", hourly_cost=100.0, max_weekly_hours=50),
        ]
        db.add_all(employees)
        
        # 3. Demand (for 7 days)
        today = date.today()
        demands = []
        for i in range(7):
            d = today + timedelta(days=i)
            # Standard daily demand
            demands.append(Demand(date=d, shift_id="S1", skill="RN", required=1))
            demands.append(Demand(date=d, shift_id="S2", skill="RN", required=1))
            demands.append(Demand(date=d, shift_id="S3", skill="ICU", required=1))
            
            # Add MD demand on day 3 (e.g., Wednesday if started Sunday)
            if i == 3:
                 demands.append(Demand(date=d, shift_id="S1", skill="MD", required=1))
            
        db.add_all(demands)
        db.commit()
        print("Database seeded with sample data (Reset & Repopulated).")
        return True, "Database seeded successfully."
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        return False, str(e)
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
