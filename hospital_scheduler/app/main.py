from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db, engine, Base
from .api.routers import employees, shifts, demands, schedules, test

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hospital Shift Scheduler", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change to specific URLs in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router, prefix="/api")
app.include_router(shifts.router, prefix="/api")
app.include_router(demands.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(test.router, prefix="/api")
