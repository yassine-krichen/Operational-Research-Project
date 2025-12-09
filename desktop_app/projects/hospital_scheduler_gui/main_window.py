import uuid
from datetime import date, datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTabWidget, QPushButton, QLabel, QFormLayout, 
                             QSpinBox, QDateEdit, QCheckBox, QDoubleSpinBox, 
                             QTextEdit, QProgressBar, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from .worker import SolverWorker
from .views.data_view import DataView
from .views.schedule_view import ScheduleView
from hospital_scheduler.app.schemas import SolveRequest
from hospital_scheduler.app.database import SessionLocal
from hospital_scheduler.app.models import ScheduleRun

class HospitalSchedulerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hospital Staff Scheduler")
        self.resize(1200, 800)
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Data Management
        self.tab_data = DataView()
        self.tabs.addTab(self.tab_data, "Data Management")
        
        # Tab 2: New Schedule
        self.tab_new = QWidget()
        self.setup_new_schedule_tab()
        self.tabs.addTab(self.tab_new, "New Schedule")
        
        # Tab 3: Execution
        self.tab_results = QWidget()
        self.setup_results_tab()
        self.tabs.addTab(self.tab_results, "Execution")
        
        # Tab 4: Visualization
        self.tab_viz = ScheduleView()
        self.tabs.addTab(self.tab_viz, "Visualization")
        
        # Tab 5: History
        self.tab_history = QWidget()
        self.setup_history_tab()
        self.tabs.addTab(self.tab_history, "History")

        # Worker
        self.worker = None

    def setup_new_schedule_tab(self):
        layout = QVBoxLayout(self.tab_new)
        
        # Form
        form_layout = QFormLayout()
        
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate())
        self.date_start.setCalendarPopup(True)
        form_layout.addRow("Start Date:", self.date_start)
        
        self.spin_days = QSpinBox()
        self.spin_days.setRange(1, 28)
        self.spin_days.setValue(7)
        form_layout.addRow("Horizon (Days):", self.spin_days)
        
        self.spin_time_limit = QSpinBox()
        self.spin_time_limit.setRange(10, 600)
        self.spin_time_limit.setValue(60)
        form_layout.addRow("Solver Time Limit (s):", self.spin_time_limit)
        
        self.check_uncovered = QCheckBox()
        self.check_uncovered.setChecked(True)
        form_layout.addRow("Allow Uncovered Demand:", self.check_uncovered)
        
        self.spin_min_rest = QDoubleSpinBox()
        self.spin_min_rest.setRange(0, 24)
        self.spin_min_rest.setValue(11)
        form_layout.addRow("Min Rest Hours:", self.spin_min_rest)

        self.spin_max_night = QSpinBox()
        self.spin_max_night.setValue(3)
        form_layout.addRow("Max Night Shifts:", self.spin_max_night)

        self.spin_min_shifts = QSpinBox()
        self.spin_min_shifts.setValue(2)
        form_layout.addRow("Min Shifts per Employee:", self.spin_min_shifts)

        self.check_weekends = QCheckBox()
        form_layout.addRow("Require Complete Weekends:", self.check_weekends)
        
        layout.addLayout(form_layout)
        
        # Action Button
        self.btn_run = QPushButton("Generate Schedule")
        self.btn_run.setStyleSheet("background-color: #2563eb; color: white; padding: 10px; font-weight: bold;")
        self.btn_run.clicked.connect(self.run_solver)
        layout.addWidget(self.btn_run)
        
        layout.addStretch()

    def setup_results_tab(self):
        layout = QVBoxLayout(self.tab_results)
        
        self.lbl_status = QLabel("Status: Idle")
        layout.addWidget(self.lbl_status)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet("background-color: #1e1e1e; color: #4ade80; font-family: Consolas;")
        layout.addWidget(self.txt_logs)

    def setup_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        
        self.btn_refresh = QPushButton("Refresh History")
        self.btn_refresh.clicked.connect(self.load_history)
        layout.addWidget(self.btn_refresh)
        
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(4)
        self.table_history.setHorizontalHeaderLabels(["Run ID", "Status", "Objective", "Created At"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_history)

    def run_solver(self):
        # 1. Gather Params
        try:
            params = SolveRequest(
                horizon_start=self.date_start.date().toPyDate(),
                horizon_days=self.spin_days.value(),
                solver_time_limit=self.spin_time_limit.value(),
                allow_uncovered_demand=self.check_uncovered.isChecked(),
                min_rest_hours=self.spin_min_rest.value(),
                max_night_shifts=self.spin_max_night.value(),
                min_shifts_per_employee=self.spin_min_shifts.value(),
                require_complete_weekends=self.check_weekends.isChecked()
            )
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", str(e))
            return

        # 2. Prepare UI
        self.tabs.setCurrentIndex(2) # Switch to Execution
        self.txt_logs.clear()
        self.progress.setRange(0, 0) # Indeterminate
        self.btn_run.setEnabled(False)
        self.lbl_status.setText("Status: Running...")

        # 3. Start Worker
        run_id = str(uuid.uuid4())
        self.worker = SolverWorker(run_id, params)
        self.worker.log_updated.connect(self.append_log)
        self.worker.finished.connect(self.on_solver_finished)
        self.worker.error.connect(self.on_solver_error)
        self.worker.start()

    def append_log(self, msg):
        self.txt_logs.append(msg)

    def on_solver_finished(self, run_id, status):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.btn_run.setEnabled(True)
        self.lbl_status.setText(f"Status: {status}")
        QMessageBox.information(self, "Solver Finished", f"Run {run_id} finished with status: {status}")
        self.load_history()
        self.tab_viz.refresh_runs() # Refresh visualization dropdown
        self.tabs.setCurrentIndex(3) # Switch to Visualization

    def on_solver_error(self, error_msg):
        self.progress.setRange(0, 100)
        self.btn_run.setEnabled(True)
        self.lbl_status.setText("Status: Error")
        QMessageBox.critical(self, "Solver Error", error_msg)

    def load_history(self):
        db = SessionLocal()
        try:
            runs = db.query(ScheduleRun).order_by(ScheduleRun.created_at.desc()).limit(50).all()
            self.table_history.setRowCount(len(runs))
            for i, run in enumerate(runs):
                self.table_history.setItem(i, 0, QTableWidgetItem(str(run.run_id)))
                self.table_history.setItem(i, 1, QTableWidgetItem(str(run.status)))
                self.table_history.setItem(i, 2, QTableWidgetItem(str(run.objective_value)))
                self.table_history.setItem(i, 3, QTableWidgetItem(str(run.created_at)))
        finally:
            db.close()
