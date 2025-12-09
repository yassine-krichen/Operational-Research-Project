from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QComboBox, QHBoxLayout, QSplitter)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt
from datetime import timedelta
from hospital_scheduler.app.database import SessionLocal
from hospital_scheduler.app.models import ScheduleRun, Assignment, Employee, Shift
from .metrics_view import MetricsView

class ScheduleView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.lbl_run = QLabel("Select Run:")
        self.combo_runs = QComboBox()
        self.combo_runs.currentIndexChanged.connect(self.load_schedule)
        controls_layout.addWidget(self.lbl_run)
        controls_layout.addWidget(self.combo_runs)
        controls_layout.addStretch()
        self.layout.addLayout(controls_layout)
        
        # Splitter for Grid and Charts
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.layout.addWidget(self.splitter)
        
        # Schedule Grid
        self.grid = QTableWidget()
        self.splitter.addWidget(self.grid)
        
        # Metrics View
        self.metrics = MetricsView()
        self.splitter.addWidget(self.metrics)
        
        # Set initial sizes (60% grid, 40% charts)
        self.splitter.setSizes([600, 400])
        
        self.refresh_runs()

    def refresh_runs(self):
        self.combo_runs.clear()
        db = SessionLocal()
        try:
            runs = db.query(ScheduleRun).filter(
                ScheduleRun.status.in_(["OPTIMAL", "FEASIBLE"])
            ).order_by(ScheduleRun.created_at.desc()).all()
            
            for run in runs:
                self.combo_runs.addItem(f"{run.created_at.strftime('%Y-%m-%d %H:%M')} - {run.run_id[:8]}", run.run_id)
        finally:
            db.close()

    def load_schedule(self):
        run_id = self.combo_runs.currentData()
        if not run_id:
            return
            
        # Update Metrics
        self.metrics.update_metrics(run_id)
            
        db = SessionLocal()
        try:
            run = db.query(ScheduleRun).filter(ScheduleRun.run_id == run_id).first()
            assignments = db.query(Assignment).filter(Assignment.run_id == run_id).all()
            employees = db.query(Employee).all()
            shifts = db.query(Shift).all()
            
            # Maps
            emp_map = {e.employee_id: e for e in employees}
            shift_map = {s.shift_id: s for s in shifts}
            
            # Setup Grid
            # Columns = Dates
            start_date = run.horizon_start
            days = run.horizon_days
            dates = [start_date + timedelta(days=i) for i in range(days)]
            
            self.grid.setColumnCount(days)
            self.grid.setHorizontalHeaderLabels([d.strftime("%a %d") for d in dates])
            
            # Rows = Employees
            self.grid.setRowCount(len(employees))
            self.grid.setVerticalHeaderLabels([e.name for e in employees])
            
            # Fill Grid
            # Create a lookup (emp_id, date) -> shift_id
            assign_lookup = {}
            for a in assignments:
                assign_lookup[(a.employee_id, a.date)] = a.shift_id
            
            # Colors for shifts
            colors = {
                "Morning": QColor("#dbeafe"), # Blue
                "Afternoon": QColor("#fef3c7"), # Amber
                "Night": QColor("#f3e8ff"), # Purple
            }
            
            for r, emp in enumerate(employees):
                for c, date_obj in enumerate(dates):
                    shift_id = assign_lookup.get((emp.employee_id, date_obj))
                    
                    if shift_id:
                        shift = shift_map.get(shift_id)
                        item = QTableWidgetItem(shift.name)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        # Color coding
                        bg_color = QColor("#e5e7eb") # Default gray
                        if shift:
                            for key, color in colors.items():
                                if key.lower() in shift.shift_type.lower() or key.lower() in shift.name.lower():
                                    bg_color = color
                                    break
                        
                        item.setBackground(QBrush(bg_color))
                        self.grid.setItem(r, c, item)
                    else:
                        # Empty/Rest
                        item = QTableWidgetItem("-")
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.grid.setItem(r, c, item)
                        
            self.grid.resizeColumnsToContents()
            
        finally:
            db.close()
