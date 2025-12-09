import sys
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime

# Import backend modules
# Note: sys.path must be set up by the main application before importing this
from hospital_scheduler.app.database import SessionLocal
from hospital_scheduler.app.services.solver import GurobiScheduler
from hospital_scheduler.app.schemas import SolveRequest
from hospital_scheduler.app.models import ScheduleRun

class SolverWorker(QThread):
    finished = pyqtSignal(str, str) # run_id, status
    error = pyqtSignal(str)
    log_updated = pyqtSignal(str)

    def __init__(self, run_id: str, params: SolveRequest):
        super().__init__()
        self.run_id = run_id
        self.params = params
        self._is_running = True

    def run(self):
        db = SessionLocal()
        try:
            # Create Run Record
            new_run = ScheduleRun(
                run_id=self.run_id,
                status="PROCESSING",
                horizon_start=self.params.horizon_start,
                horizon_days=self.params.horizon_days,
                solver_params=self.params.model_dump(mode='json'),
                created_at=datetime.utcnow()
            )
            db.add(new_run)
            db.commit()

            # Initialize Scheduler
            scheduler = GurobiScheduler(db, self.run_id, self.params)
            
            # Monkey patch the log method to emit signals
            original_log = scheduler.log
            def custom_log(msg: str):
                original_log(msg)
                self.log_updated.emit(msg)
            scheduler.log = custom_log

            # Run Solver
            scheduler.solve()
            
            # Check final status
            db.refresh(new_run)
            self.finished.emit(self.run_id, new_run.status)

        except Exception as e:
            traceback.print_exc()
            self.error.emit(str(e))
        finally:
            db.close()

    def stop(self):
        self._is_running = False
        # Note: Gurobi has its own termination mechanism (model.terminate()), 
        # but we'd need access to the model instance which is inside the scheduler.
        # For now, we just let the thread finish naturally or kill it (unsafe).
