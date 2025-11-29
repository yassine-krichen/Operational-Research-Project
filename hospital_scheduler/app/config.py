import os

class Settings:
    PROJECT_NAME: str = "Hospital Shift Scheduler"
    PROJECT_VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hospital_scheduler.db")

settings = Settings()
