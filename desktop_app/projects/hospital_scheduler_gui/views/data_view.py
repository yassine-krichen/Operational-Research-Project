from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QTabWidget, QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from hospital_scheduler.app.database import SessionLocal
from hospital_scheduler.app.models import Employee, Shift
from hospital_scheduler.seed import seed_data

class DataView(QWidget):
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Employees Tab
        self.tab_employees = QWidget()
        self.setup_employees_tab()
        self.tabs.addTab(self.tab_employees, "Employees")
        
        # Shifts Tab
        self.tab_shifts = QWidget()
        self.setup_shifts_tab()
        self.tabs.addTab(self.tab_shifts, "Shifts")
        
        # Buttons Layout
        btn_layout = QHBoxLayout()
        
        # Refresh Button
        self.btn_refresh = QPushButton("Refresh Data")
        self.btn_refresh.clicked.connect(self.load_data)
        btn_layout.addWidget(self.btn_refresh)
        
        # Seed Button
        self.btn_seed = QPushButton("Seed Database (Reset)")
        self.btn_seed.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold;")
        self.btn_seed.clicked.connect(self.run_seed)
        btn_layout.addWidget(self.btn_seed)
        
        self.layout.addLayout(btn_layout)
        
        self.load_data()

    def run_seed(self):
        reply = QMessageBox.question(self, 'Seed Database', 
                                     "This will DELETE ALL EXISTING DATA and repopulate with sample data. Continue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success, msg = seed_data()
            if success:
                QMessageBox.information(self, "Success", msg)
                self.load_data()
                self.data_changed.emit()
            else:
                QMessageBox.critical(self, "Error", f"Failed to seed: {msg}")

    def setup_employees_tab(self):
        layout = QVBoxLayout(self.tab_employees)
        self.table_emp = QTableWidget()
        self.table_emp.setColumnCount(5)
        self.table_emp.setHorizontalHeaderLabels(["ID", "Name", "Role", "Skills", "Hourly Cost"])
        self.table_emp.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_emp)

    def setup_shifts_tab(self):
        layout = QVBoxLayout(self.tab_shifts)
        self.table_shifts = QTableWidget()
        self.table_shifts.setColumnCount(5)
        self.table_shifts.setHorizontalHeaderLabels(["ID", "Name", "Start", "End", "Type"])
        self.table_shifts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_shifts)

    def load_data(self):
        db = SessionLocal()
        try:
            # Load Employees
            employees = db.query(Employee).all()
            self.table_emp.setRowCount(len(employees))
            for i, emp in enumerate(employees):
                self.table_emp.setItem(i, 0, QTableWidgetItem(str(emp.employee_id)))
                self.table_emp.setItem(i, 1, QTableWidgetItem(str(emp.name)))
                self.table_emp.setItem(i, 2, QTableWidgetItem(str(emp.role)))
                self.table_emp.setItem(i, 3, QTableWidgetItem(str(emp.skills)))
                self.table_emp.setItem(i, 4, QTableWidgetItem(str(emp.hourly_cost)))
            
            # Load Shifts
            shifts = db.query(Shift).all()
            self.table_shifts.setRowCount(len(shifts))
            for i, s in enumerate(shifts):
                self.table_shifts.setItem(i, 0, QTableWidgetItem(str(s.shift_id)))
                self.table_shifts.setItem(i, 1, QTableWidgetItem(str(s.name)))
                self.table_shifts.setItem(i, 2, QTableWidgetItem(str(s.start_time)))
                self.table_shifts.setItem(i, 3, QTableWidgetItem(str(s.end_time)))
                self.table_shifts.setItem(i, 4, QTableWidgetItem(str(s.shift_type)))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
        finally:
            db.close()
