import uuid
from datetime import date, datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTabWidget, QPushButton, QLabel, QFormLayout, 
                             QSpinBox, QDateEdit, QCheckBox, QDoubleSpinBox, 
                             QTextEdit, QProgressBar, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, QDate
from .worker import SolverWorker
from .views.data_view import DataView
from .views.schedule_view import ScheduleView
from .views.demands_view import DemandsView
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
        
        # Tab 2: Demands
        self.tab_demands = DemandsView()
        self.tabs.addTab(self.tab_demands, "Demands")
        
        # Connect signals
        self.tab_data.data_changed.connect(self.tab_demands.refresh_data)
        
        # Tab 3: New Schedule
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
        # Scroll Area for smaller screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        main_layout = QVBoxLayout(self.tab_new)
        main_layout.addWidget(scroll)
        
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        
        # --- Section 1: Schedule Parameters ---
        grp_params = QGroupBox("📅 Schedule Parameters")
        grp_params.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout_params = QFormLayout(grp_params)
        layout_params.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate())
        self.date_start.setCalendarPopup(True)
        self.add_form_row(layout_params, "Start Date:", self.date_start, "The first day of the schedule.")
        
        self.spin_days = QSpinBox()
        self.spin_days.setRange(1, 28)
        self.spin_days.setValue(7)
        self.add_form_row(layout_params, "Horizon (Days):", self.spin_days, "Duration of the schedule (e.g., 7 days, 14 days).")
        
        layout.addWidget(grp_params)

        # --- Section 2: Solver Configuration ---
        grp_solver = QGroupBox("⚙️ Solver Configuration")
        grp_solver.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout_solver = QFormLayout(grp_solver)
        layout_solver.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.spin_time_limit = QSpinBox()
        self.spin_time_limit.setRange(10, 600)
        self.spin_time_limit.setValue(60)
        self.add_form_row(layout_solver, "Time Limit (s):", self.spin_time_limit, "Max time for Gurobi to find a solution.")
        
        self.check_uncovered = QCheckBox("Allow Uncovered Demand")
        self.check_uncovered.setChecked(True)
        self.check_uncovered.setToolTip("If checked, the solver can leave shifts empty (with a penalty) if no staff is available.")
        layout_solver.addRow("", self.check_uncovered)
        
        self.spin_penalty = QDoubleSpinBox()
        self.spin_penalty.setRange(0, 10000)
        self.spin_penalty.setValue(1000)
        self.add_form_row(layout_solver, "Uncovered Penalty:", self.spin_penalty, "Cost added to objective for each missing shift.")

        self.spin_weight_pref = QDoubleSpinBox()
        self.spin_weight_pref.setRange(0, 1000)
        self.spin_weight_pref.setValue(50)
        self.add_form_row(layout_solver, "Preference Weight:", self.spin_weight_pref, "Penalty for ignoring employee 'avoid' requests.")
        
        layout.addWidget(grp_solver)

        # --- Section 3: Work Rules ---
        grp_rules = QGroupBox("⚖️ Work Rules & Constraints")
        grp_rules.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout_rules = QFormLayout(grp_rules)
        layout_rules.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.spin_consecutive = QSpinBox()
        self.spin_consecutive.setRange(1, 14)
        self.spin_consecutive.setValue(5)
        self.add_form_row(layout_rules, "Max Consecutive Days:", self.spin_consecutive, "Max days an employee can work in a row.")

        self.spin_min_rest = QDoubleSpinBox()
        self.spin_min_rest.setRange(0, 24)
        self.spin_min_rest.setValue(11)
        self.add_form_row(layout_rules, "Min Rest Hours:", self.spin_min_rest, "Minimum hours between shifts (e.g., 11h).")

        self.spin_max_night = QSpinBox()
        self.spin_max_night.setRange(0, 7)
        self.spin_max_night.setValue(3)
        self.add_form_row(layout_rules, "Max Night Shifts:", self.spin_max_night, "Max night shifts per employee in the horizon.")
        
        layout.addWidget(grp_rules)

        # --- Section 4: Fairness & Policy ---
        grp_fairness = QGroupBox("🤝 Fairness & Policy")
        grp_fairness.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout_fairness = QFormLayout(grp_fairness)
        layout_fairness.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.spin_min_shifts = QSpinBox()
        self.spin_min_shifts.setRange(0, 7)
        self.spin_min_shifts.setValue(2)
        self.add_form_row(layout_fairness, "Min Shifts/Employee:", self.spin_min_shifts, "Ensure everyone gets at least this many shifts.")

        self.check_weekends = QCheckBox("Require Complete Weekends")
        self.check_weekends.setToolTip("If an employee works Saturday, they must work Sunday (and vice versa).")
        layout_fairness.addRow("", self.check_weekends)
        
        layout.addWidget(grp_fairness)
        
        # Action Button
        self.btn_run = QPushButton("🚀 Generate Schedule")
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #2563eb; 
                color: white; 
                padding: 12px; 
                font-weight: bold;
                font-size: 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #9ca3af; }
        """)
        self.btn_run.clicked.connect(self.run_solver)
        layout.addWidget(self.btn_run)
        
        layout.addStretch()

    def add_form_row(self, layout, label_text, widget, tooltip):
        """Helper to add a row with a label, widget, and tooltip."""
        widget.setToolTip(tooltip)
        # Create a label with a help icon or just tooltip on hover
        lbl = QLabel(label_text)
        lbl.setToolTip(tooltip)
        layout.addRow(lbl, widget)

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
                penalty_uncovered=self.spin_penalty.value(),
                weight_preference=self.spin_weight_pref.value(),
                max_consecutive_days=self.spin_consecutive.value(),
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
