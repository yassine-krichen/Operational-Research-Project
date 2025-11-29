from fastapi import FastAPI
from .api.endpoints import router as api_router
from .database import init_db, engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hospital Shift Scheduler", version="1.0.0")

app.include_router(api_router, prefix="/api")
