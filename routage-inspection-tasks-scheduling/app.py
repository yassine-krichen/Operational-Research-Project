# app.py
"""
Comprehensive Inspection Routing Optimization Application
Multi-tab interface with dashboard, data management, visualization, and analytics.
"""

import sys
import time
from datetime import datetime
from typing import Optional, Dict, List

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox,
    QComboBox, QLineEdit, QMessageBox, QProgressBar, QTextEdit, QGroupBox,
    QCheckBox, QListWidget, QListWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from dataset_generator import DatasetGenerator
from optimizer import solve_routing, compute_distance_matrix
from models import Inspector, Task, Depot


class SolverThread(QThread):
    """Background thread for optimization solving."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    
    def __init__(self, inspectors, tasks, depot, time_limit, speed_kmh=40.0, use_depot_start: bool = False):
        super().__init__()
        self.inspectors = inspectors
        self.tasks = tasks
        self.depot = depot
        self.time_limit = time_limit
        self.speed_kmh = speed_kmh
        self.use_depot_start = use_depot_start
    
    def run(self):
        try:
            solution = solve_routing(
                self.inspectors,
                self.tasks,
                self.depot,
                time_limit=self.time_limit,
                speed_kmh=self.speed_kmh,
                use_depot_start=self.use_depot_start
            )
            self.result.emit(solution)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class DashboardTab(QWidget):
    """Main dashboard with solver controls and key metrics."""
    
    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.solver_thread = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Inspection Routing Optimization Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Control Panel
        control_group = QGroupBox("Solver Controls")
        control_layout = QHBoxLayout()
        
        time_label = QLabel("Time Limit (s):")
        self.time_spinbox = QSpinBox()
        self.time_spinbox.setRange(10, 300)
        self.time_spinbox.setValue(60)
        
        speed_label = QLabel("Speed (km/h):")
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(10, 200)
        self.speed_spinbox.setValue(40.0)
        self.speed_spinbox.setSingleStep(5)
        
        # Option: force all inspectors to start/return at depot
        self.depot_start_cb = QCheckBox("Start/return at depot")
        self.depot_start_cb.setChecked(False)
        # update shared app flag when toggled
        self.depot_start_cb.stateChanged.connect(lambda s: setattr(self.app, 'use_depot_start', s == Qt.Checked))
        
        self.solve_btn = QPushButton("Solve Optimization")
        self.solve_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.solve_btn.clicked.connect(self.solve_optimization)
        
        self.export_btn = QPushButton("Export Solution")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_solution)
        
        control_layout.addWidget(time_label)
        control_layout.addWidget(self.time_spinbox)
        control_layout.addWidget(speed_label)
        control_layout.addWidget(self.speed_spinbox)
        control_layout.addWidget(self.depot_start_cb)
        control_layout.addWidget(self.solve_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Metrics
        metrics_group = QGroupBox("Solution Metrics")
        metrics_layout = QHBoxLayout()
        
        self.metric_labels = {}
        metrics = [
            ("Objective Value", "—"),
            ("Travel Time", "—"),
            ("Service Time", "—"),
            ("Total Routes", "—"),
            ("Solver Status", "—"),
            ("Solve Time", "—"),
        ]
        
        for metric_name, value in metrics:
            metric_widget = QWidget()
            metric_vbox = QVBoxLayout()
            label = QLabel(metric_name)
            label.setStyleSheet("font-weight: bold; color: #333;")
            value_label = QLabel(value)
            value_label.setStyleSheet("font-size: 14px; color: #4CAF50;")
            metric_vbox.addWidget(label)
            metric_vbox.addWidget(value_label)
            metric_widget.setLayout(metric_vbox)  # **FIX**: Set the layout on the widget
            metrics_layout.addWidget(metric_widget)
            self.metric_labels[metric_name] = value_label
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Status log
        log_group = QGroupBox("Status Log")
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(150)
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.status_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def log_status(self, message: str):
        """Add message to status log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_log.append(f"[{timestamp}] {message}")
    
    def solve_optimization(self):
        """Trigger optimization solver."""
        if not self.app.tasks or not self.app.inspectors:
            QMessageBox.warning(self, "Missing Data", "Please load or create tasks and inspectors first.")
            return
        
        self.solve_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.log_status(f"Starting optimization with {len(self.app.inspectors)} inspectors and {len(self.app.tasks)} tasks...")
        
        time_limit = self.time_spinbox.value()
        speed_kmh = self.speed_spinbox.value()
        self.solver_thread = SolverThread(
            self.app.inspectors,
            self.app.tasks,
            self.app.depot,
            time_limit,
            speed_kmh,
            use_depot_start=self.app.use_depot_start
        )
        self.solver_thread.result.connect(self.on_solution_ready)
        self.solver_thread.error.connect(self.on_solver_error)
        self.solver_thread.finished.connect(self.on_solver_finished)
        self.solver_thread.start()
    
    def on_solution_ready(self, solution):
        """Handle solution result."""
        self.app.current_solution = solution
        self.export_btn.setEnabled(True)
        
        # Update metrics
        self.metric_labels["Objective Value"].setText(f"{solution.objective_value:.3f}")
        self.metric_labels["Travel Time"].setText(f"{solution.total_travel_time:.2f} h")
        self.metric_labels["Service Time"].setText(f"{solution.total_service_time:.2f} h")
        self.metric_labels["Total Routes"].setText(f"{len(solution.routes)}")
        self.metric_labels["Solver Status"].setText(solution.solver_status)
        self.metric_labels["Solve Time"].setText(f"{solution.solve_time:.2f} s")
        
        self.log_status("✓ Optimization completed successfully!")
        
        # Show success message with mode info
        mode_info = "depot start/return" if getattr(self.app, 'use_depot_start', False) else "inspector home locations"
        QMessageBox.information(self, "Success", f"Optimization completed successfully!\n\nMode: {mode_info}")
    
    def on_solver_error(self, error_msg: str):
        """Handle solver error."""
        self.log_status(f"✗ Error: {error_msg}")
        
        # Add helpful context based on depot start mode
        mode_hint = ""
        if getattr(self.app, 'use_depot_start', False):
            mode_hint = "\n\n💡 TIP: You have 'Start/return at depot' enabled.\nIf the depot is far from tasks, try:\n• Unchecking the depot option\n• Moving the depot closer to tasks\n• Increasing max_work_hours or availability windows"
        
        QMessageBox.critical(self, "Solver Error", error_msg + mode_hint)
    
    def on_solver_finished(self):
        """Handle solver completion."""
        self.solve_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def export_solution(self):
        """Export solution to text file."""
        if not self.app.current_solution:
            return
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Solution", "", "Text Files (*.txt)"
        )
        if not filename:
            return
        
        try:
            with open(filename, 'w') as f:
                f.write("=" * 70 + "\n")
                f.write("INSPECTION ROUTING OPTIMIZATION SOLUTION\n")
                f.write("=" * 70 + "\n\n")
                
                sol = self.app.current_solution
                f.write(sol.summary() + "\n\n")
                
                f.write("-" * 70 + "\n")
                f.write("DETAILED ROUTES\n")
                f.write("-" * 70 + "\n\n")
                
                for ins_id, route_sol in sol.routes.items():
                    f.write(f"Inspector: {ins_id}\n")
                    f.write(f"  Route: {route_sol.route}\n")
                    f.write(f"  Travel Time: {route_sol.travel_time:.2f} h\n")
                    f.write(f"  Service Time: {route_sol.service_time:.2f} h\n")
                    f.write(f"  Total Time: {route_sol.total_time:.2f} h\n")
                    f.write(f"  Tasks Completed: {route_sol.tasks_completed}\n\n")
            
            self.log_status(f"✓ Solution exported to {filename}")
            QMessageBox.information(self, "Export Successful", f"Solution exported to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))


class InspectorsTab(QWidget):
    """Inspector management interface."""
    
    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Inspector Management")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Controls
        control_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Inspector")
        add_btn.clicked.connect(self.add_inspector)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_inspector)
        
        generate_btn = QPushButton("Generate Random")
        generate_btn.clicked.connect(self.generate_random)
        
        control_layout.addWidget(add_btn)
        control_layout.addWidget(delete_btn)
        control_layout.addWidget(generate_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Skills", "Max Hours", "Location (x, y)", "Availability"
        ])
        # Set fixed column widths for consistent appearance
        self.table.setColumnWidth(0, 50)    # ID
        self.table.setColumnWidth(1, 120)   # Name
        self.table.setColumnWidth(2, 140)   # Skills
        self.table.setColumnWidth(3, 90)    # Max Hours
        self.table.setColumnWidth(4, 130)   # Location
        self.table.setColumnWidth(5, 130)   # Availability
        self.table.horizontalHeader().setStretchLastSection(False)
        
        # Enable cell editing and connect signal to save changes
        self.table.itemChanged.connect(self.on_cell_changed)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def on_cell_changed(self, item):
        """Handle cell edits and update inspector data."""
        try:
            row = item.row()
            col = item.column()
            if row >= len(self.app.inspectors):
                return
            
            inspector = self.app.inspectors[row]
            value = item.text()
            
            # Update the appropriate field
            if col == 1:  # Name
                inspector.name = value
            elif col == 3:  # Max Hours
                inspector.max_work_hours = float(value)
            elif col == 4:  # Location
                # Parse "(x, y)" format
                value = value.strip("()")
                parts = value.split(",")
                if len(parts) == 2:
                    inspector.location = (float(parts[0].strip()), float(parts[1].strip()))
        except Exception as e:
            print(f"Error updating inspector: {e}")
    
    def refresh_table(self):
        """Refresh inspector table."""
        # Temporarily disconnect signal to avoid triggering during refresh
        self.table.itemChanged.disconnect(self.on_cell_changed)
        
        self.table.setRowCount(len(self.app.inspectors))
        for row, inspector in enumerate(self.app.inspectors):
            self.table.setItem(row, 0, QTableWidgetItem(inspector.id))
            self.table.setItem(row, 1, QTableWidgetItem(inspector.name))
            self.table.setItem(row, 2, QTableWidgetItem(", ".join(inspector.skills)))
            self.table.setItem(row, 3, QTableWidgetItem(f"{inspector.max_work_hours:.1f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"({inspector.location[0]:.1f}, {inspector.location[1]:.1f})"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{inspector.availability_start}:00 - {inspector.availability_end}:00"))
        
        # Reconnect signal
        self.table.itemChanged.connect(self.on_cell_changed)
    
    def add_inspector(self):
        """Add new inspector."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Inspector")
        layout = QVBoxLayout()
        
        inputs = {}
        fields = ["ID", "Name", "Max Hours", "X Coordinate", "Y Coordinate"]
        for field in fields:
            hlayout = QHBoxLayout()
            hlayout.addWidget(QLabel(field))
            if field == "Max Hours":
                widget = QDoubleSpinBox()
                widget.setRange(1, 24)
                widget.setValue(8.0)
            elif field in ["X Coordinate", "Y Coordinate"]:
                widget = QDoubleSpinBox()
                widget.setRange(0, 100)
                widget.setValue(50.0)
            else:
                widget = QLineEdit()
            hlayout.addWidget(widget)
            inputs[field] = widget
            layout.addLayout(hlayout)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        if dialog.exec_():
            try:
                inspector = Inspector(
                    id=inputs["ID"].text(),
                    name=inputs["Name"].text(),
                    skills=["electrical", "quality"],  # Default skills
                    max_work_hours=inputs["Max Hours"].value(),
                    location=(inputs["X Coordinate"].value(), inputs["Y Coordinate"].value()),
                    availability_start=6,
                    availability_end=18,
                )
                self.app.inspectors.append(inspector)
                self.refresh_table()
                # Update inspector filters in VisualizationTab
                viz_tab = self.app.tabs.widget(3)  # Routes Map tab
                if hasattr(viz_tab, 'rebuild_inspector_filters'):
                    viz_tab.rebuild_inspector_filters()
                QMessageBox.information(self, "Success", "Inspector added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def delete_inspector(self):
        """Delete selected inspector."""
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select an inspector to delete.")
            return
        
        row = selected[0].row()
        del self.app.inspectors[row]
        self.refresh_table()
        # Update inspector filters in VisualizationTab
        viz_tab = self.app.tabs.widget(3)  # Routes Map tab
        if hasattr(viz_tab, 'rebuild_inspector_filters'):
            viz_tab.rebuild_inspector_filters()
    
    def generate_random(self):
        """Generate random inspectors."""
        count, ok = QtWidgets.QInputDialog.getInt(
            self, "Generate Inspectors", "Number of inspectors:", 3, 1, 20
        )
        if ok:
            gen = DatasetGenerator()
            self.app.inspectors = gen.generate_inspectors(count=count, structured=False)
            self.refresh_table()
            # Update inspector filters in VisualizationTab
            viz_tab = self.app.tabs.widget(3)  # Routes Map tab
            if hasattr(viz_tab, 'rebuild_inspector_filters'):
                viz_tab.rebuild_inspector_filters()
            QMessageBox.information(self, "Success", f"Generated {count} inspectors!")


class TasksTab(QWidget):
    """Task management interface."""
    
    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Task Management")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Controls
        control_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Task")
        add_btn.clicked.connect(self.add_task)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_task)
        
        generate_btn = QPushButton("Generate Random")
        generate_btn.clicked.connect(self.generate_random)
        
        control_layout.addWidget(add_btn)
        control_layout.addWidget(delete_btn)
        control_layout.addWidget(generate_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Location (x,y)", "Duration (h)", "Skill", "Difficulty", "Time Window", "Priority"
        ])
        # Set fixed column widths for consistent appearance
        self.table.setColumnWidth(0, 50)    # ID
        self.table.setColumnWidth(1, 130)   # Name
        self.table.setColumnWidth(2, 120)   # Location
        self.table.setColumnWidth(3, 85)    # Duration
        self.table.setColumnWidth(4, 85)    # Skill
        self.table.setColumnWidth(5, 80)    # Difficulty
        self.table.setColumnWidth(6, 110)   # Time Window
        self.table.setColumnWidth(7, 70)    # Priority
        self.table.horizontalHeader().setStretchLastSection(False)
        
        # Enable cell editing and connect signal to save changes
        self.table.itemChanged.connect(self.on_cell_changed)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def on_cell_changed(self, item):
        """Handle cell edits and update task data."""
        try:
            row = item.row()
            col = item.column()
            if row >= len(self.app.tasks):
                return
            
            task = self.app.tasks[row]
            value = item.text()
            
            # Update the appropriate field
            if col == 1:  # Name
                task.name = value
            elif col == 2:  # Location
                # Parse "(x, y)" format
                value = value.strip("()")
                parts = value.split(",")
                if len(parts) == 2:
                    task.x = float(parts[0].strip())
                    task.y = float(parts[1].strip())
            elif col == 3:  # Duration
                task.duration = float(value)
            elif col == 4:  # Skill
                task.required_skill = value.strip()
            elif col == 5:  # Difficulty
                task.difficulty = int(value)
            elif col == 7:  # Priority
                task.priority = int(value)
        except Exception as e:
            print(f"Error updating task: {e}")
    
    def refresh_table(self):
        """Refresh task table."""
        # Temporarily disconnect signal to avoid triggering during refresh
        self.table.itemChanged.disconnect(self.on_cell_changed)
        
        self.table.setRowCount(len(self.app.tasks))
        for row, task in enumerate(self.app.tasks):
            self.table.setItem(row, 0, QTableWidgetItem(str(task.id)))
            self.table.setItem(row, 1, QTableWidgetItem(task.name))
            self.table.setItem(row, 2, QTableWidgetItem(f"({task.x:.1f}, {task.y:.1f})"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{task.duration:.1f}"))
            self.table.setItem(row, 4, QTableWidgetItem(task.required_skill))
            self.table.setItem(row, 5, QTableWidgetItem(str(task.difficulty)))
            self.table.setItem(row, 6, QTableWidgetItem(f"{task.tw_start}:00 - {task.tw_end}:00"))
            self.table.setItem(row, 7, QTableWidgetItem(str(task.priority)))
        
        # Reconnect signal
        self.table.itemChanged.connect(self.on_cell_changed)
    
    def add_task(self):
        """Add new task."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Task")
        layout = QVBoxLayout()
        
        inputs = {}
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Name:"))
        inputs["Name"] = QLineEdit()
        hlayout.addWidget(inputs["Name"])
        layout.addLayout(hlayout)
        
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("X Coordinate:"))
        inputs["X"] = QDoubleSpinBox()
        inputs["X"].setRange(0, 100)
        inputs["X"].setValue(50)
        hlayout.addWidget(inputs["X"])
        layout.addLayout(hlayout)
        
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Y Coordinate:"))
        inputs["Y"] = QDoubleSpinBox()
        inputs["Y"].setRange(0, 100)
        inputs["Y"].setValue(50)
        hlayout.addWidget(inputs["Y"])
        layout.addLayout(hlayout)
        
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Duration (hours):"))
        inputs["Duration"] = QDoubleSpinBox()
        inputs["Duration"].setRange(0.25, 8)
        inputs["Duration"].setValue(1.0)
        hlayout.addWidget(inputs["Duration"])
        layout.addLayout(hlayout)
        
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Required Skill:"))
        inputs["Skill"] = QComboBox()
        inputs["Skill"].addItems(["electrical", "quality", "safety", "structural"])
        hlayout.addWidget(inputs["Skill"])
        layout.addLayout(hlayout)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        if dialog.exec_():
            try:
                max_id = max([t.id for t in self.app.tasks], default=0)
                task = Task(
                    id=max_id + 1,
                    name=inputs["Name"].text(),
                    x=inputs["X"].value(),
                    y=inputs["Y"].value(),
                    duration=inputs["Duration"].value(),
                    required_skill=inputs["Skill"].currentText(),
                    difficulty=2,
                    tw_start=8,
                    tw_end=17,
                )
                self.app.tasks.append(task)
                self.refresh_table()
                QMessageBox.information(self, "Success", "Task added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def delete_task(self):
        """Delete selected task."""
        selected = self.table.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a task to delete.")
            return
        
        row = selected[0].row()
        del self.app.tasks[row]
        self.refresh_table()
    
    def generate_random(self):
        """Generate random tasks."""
        count, ok = QtWidgets.QInputDialog.getInt(
            self, "Generate Tasks", "Number of tasks:", 10, 1, 50
        )
        if ok:
            gen = DatasetGenerator()
            self.app.tasks = gen.generate_tasks(count=count, structured=False)
            self.refresh_table()
            QMessageBox.information(self, "Success", f"Generated {count} tasks!")


class VisualizationTab(QWidget):
    """Route visualization with matplotlib."""
    
    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Route Visualization")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Controls
        control_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh Map")
        refresh_btn.clicked.connect(self.plot_routes)
        
        self.show_distance_cb = QCheckBox("Show Distances")
        self.show_distance_cb.setChecked(False)
        self.show_distance_cb.stateChanged.connect(self.plot_routes)

        # Toggle for showing sequence numbers on the map
        self.show_sequence_cb = QCheckBox("Show Sequence Numbers")
        self.show_sequence_cb.setChecked(True)
        self.show_sequence_cb.stateChanged.connect(self.plot_routes)
        
        # Inspector filter checkboxes
        filter_label = QLabel("Show Inspectors:")
        self.inspector_filters = {}
        self.inspector_filter_layout = QHBoxLayout()
        self.rebuild_inspector_filters()
        
        control_layout.addWidget(refresh_btn)
        control_layout.addWidget(self.show_distance_cb)
        control_layout.addWidget(self.show_sequence_cb)
        control_layout.addWidget(filter_label)
        control_layout.addLayout(self.inspector_filter_layout)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # Canvas with toolbar
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
    
    def rebuild_inspector_filters(self):
        """Rebuild inspector filter checkboxes based on current inspectors."""
        # Clear existing checkboxes
        while self.inspector_filter_layout.count():
            child = self.inspector_filter_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.inspector_filters.clear()
        
        # Create checkbox for each inspector
        for inspector in self.app.inspectors:
            cb = QCheckBox(inspector.id)
            cb.setChecked(True)
            cb.stateChanged.connect(self.plot_routes)
            self.inspector_filters[inspector.id] = cb
            self.inspector_filter_layout.addWidget(cb)
    
    def plot_routes(self):
        """Plot routes on map."""
        if not self.app.current_solution:
            QMessageBox.warning(self, "No Solution", "Please solve the optimization first.")
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        solution = self.app.current_solution
        # Enhanced color palette for better distinction
        colors = ["#2ca02c", "#9467bd", "#ff7f0e", "#d62728", "#1f77b4", "#8c564b", "#e377c2"]  # Green, Violet, Orange first
        linestyles = ["-", "--", "-.", ":", "-", "--", "-."]  # Vary line styles per inspector
        show_distances = self.show_distance_cb.isChecked()
        
        # Plot depot with prominent marker (only if used)
        ax.scatter(self.app.depot.x, self.app.depot.y, c="red", s=250, marker="s", 
                  label="Depot", zorder=6, edgecolors='black', linewidths=2)
        ax.text(self.app.depot.x, self.app.depot.y - 3, 'DEPOT', 
               fontsize=9, fontweight='bold', color='darkred', ha='center')
        
        # Map inspector ID to color for consistency
        inspector_colors = {}
        for idx, inspector in enumerate(self.app.inspectors):
            inspector_colors[inspector.id] = colors[idx % len(colors)]
        
        # Plot inspector starting locations with matching route colors (unless using depot)
        if not getattr(self.app, 'use_depot_start', False):
            for idx, inspector in enumerate(self.app.inspectors):
                color = inspector_colors[inspector.id]
                ax.scatter(inspector.location[0], inspector.location[1], c=color, s=180, marker="^", 
                          zorder=6, edgecolors='black', linewidths=1.5)
                ax.text(inspector.location[0], inspector.location[1] - 2.5, 
                       f'{inspector.id}', fontsize=9, fontweight='bold', color=color, ha='center')
        
        # Plot all tasks as light background reference (unassigned appearance)
        for task in self.app.tasks:
            ax.scatter(task.x, task.y, c="lightgray", s=60, zorder=2, edgecolors='#aaa', linewidths=0.5)
        
        # Plot routes with distinct styles
        for idx, (ins_id, route_sol) in enumerate(solution.routes.items()):
            # Check if this inspector should be shown
            if hasattr(self, 'inspector_filters') and ins_id in self.inspector_filters:
                if not self.inspector_filters[ins_id].isChecked():
                    continue
            
            if not route_sol.route:
                continue
            
            # Get inspector's starting location
            inspector = next((i for i in self.app.inspectors if i.id == ins_id), None)
            if not inspector:
                continue
            
            color = inspector_colors.get(ins_id, colors[idx % len(colors)])
            linestyle = linestyles[idx % len(linestyles)]
            
            # Build coordinates starting from inspector's location or depot depending on setting
            if getattr(self.app, 'use_depot_start', False):
                start_point = (self.app.depot.x, self.app.depot.y)
            else:
                start_point = (inspector.location[0], inspector.location[1])
            coords = [start_point]
            for task_id in route_sol.route:
                if task_id == 0:
                    continue
                task = next((t for t in self.app.tasks if t.id == task_id), None)
                if task:
                    coords.append((task.x, task.y))
            # Return to starting point (depot or inspector home)
            coords.append(start_point)
            
            # Plot route line with distinct color and line style
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            ax.plot(xs, ys, linestyle=linestyle, color=color, label=ins_id, 
                   linewidth=2.5, alpha=0.7, zorder=3)
            
            # Draw colored markers on each visited task with task ID inside
            visited_tasks = [tid for tid in route_sol.route if tid != 0]
            for tid in visited_tasks:
                task = next((t for t in self.app.tasks if t.id == tid), None)
                if task:
                    # Task marker with task ID inside
                    ax.scatter(task.x, task.y, c=color, s=280, zorder=7, 
                              edgecolors='white', linewidths=2)
                    ax.text(task.x, task.y, str(tid), fontsize=10, fontweight='bold',
                           color='white', ha='center', va='center', zorder=8)
            
            # Add distance labels if enabled (smaller, less intrusive)
            if show_distances:
                import math
                for i in range(len(coords) - 1):
                    x1, y1 = coords[i]
                    x2, y2 = coords[i + 1]
                    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                    ax.text(mid_x, mid_y, f"{distance:.0f}", fontsize=6, 
                           bbox=dict(boxstyle="round,pad=0.15", facecolor="white", 
                                   edgecolor=color, alpha=0.8), zorder=9)
            
            # Draw directional arrows (subtle)
            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                # Place arrow at 60% of the way along the line
                mx = x1 + 0.6 * (x2 - x1)
                my = y1 + 0.6 * (y2 - y1)
                dx = (x2 - x1) * 0.15
                dy = (y2 - y1) * 0.15
                ax.annotate('', xy=(mx + dx, my + dy), xytext=(mx, my), 
                           arrowprops=dict(arrowstyle='->', color=color, lw=1.5), zorder=4)
        
        ax.set_xlabel("X Coordinate (km)", fontsize=11, fontweight='bold')
        ax.set_ylabel("Y Coordinate (km)", fontsize=11, fontweight='bold')
        ax.set_title("Inspector Routes Map", fontsize=13, fontweight='bold', pad=15)
        ax.legend(loc="best", fontsize=10, framealpha=0.95)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_aspect('equal', adjustable='datalim')
        self.figure.tight_layout()
        self.canvas.draw()
class DistancesTab(QWidget):
    """Distance matrix display between all locations."""
    
    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Distance Matrix")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Controls
        control_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh Distances")
        refresh_btn.clicked.connect(self.update_distances)
        
        speed_label = QLabel("Speed (km/h):")
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(10, 200)
        self.speed_spinbox.setValue(40.0)
        self.speed_spinbox.setSingleStep(5)
        self.speed_spinbox.valueChanged.connect(self.update_distances)
        
        control_layout.addWidget(refresh_btn)
        control_layout.addWidget(speed_label)
        control_layout.addWidget(self.speed_spinbox)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # Distance table
        self.distance_table = QTableWidget()
        layout.addWidget(self.distance_table)
        
        self.setLayout(layout)
        self.update_distances()
    
    def update_distances(self):
        """Update and display distance matrix."""
        if not self.app.tasks or not self.app.inspectors:
            self.distance_table.setRowCount(0)
            self.distance_table.setColumnCount(0)
            return
        
        speed_kmh = self.speed_spinbox.value()
        
        # Compute distance matrix (respect depot-start toggle)
        dist_data = compute_distance_matrix(
            self.app.inspectors,
            self.app.tasks,
            self.app.depot,
            speed_kmh=speed_kmh,
            use_depot_start=getattr(self.app, 'use_depot_start', False)
        )
        
        dist_matrices = dist_data["distance"]  # List of distance matrices, one per inspector
        # For display, use the first inspector's matrix (or could average them)
        dist_matrix = dist_matrices[0]
        n = dist_data["num_nodes"]
        
        # Create labels for rows/columns
        if getattr(self.app, 'use_depot_start', False):
            labels = ["Depot"]
        else:
            labels = [f"{self.app.inspectors[0].id}_Start"]
        for task in self.app.tasks:
            labels.append(f"T{task.id}")
        
        # Set up table
        self.distance_table.setRowCount(n)
        self.distance_table.setColumnCount(n)
        self.distance_table.setHorizontalHeaderLabels(labels)
        self.distance_table.setVerticalHeaderLabels(labels)
        
        # Populate table with distances
        for i in range(n):
            for j in range(n):
                distance = dist_matrix[i][j]
                item = QTableWidgetItem(f"{distance:.2f}h")
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Arial", 9))
                
                # Color code with gradient: diagonal, short, medium, long
                if i == j:
                    item.setBackground(QColor(211, 211, 211))  # Light gray diagonal
                elif distance < 0.5:
                    item.setBackground(QColor(0, 200, 0))      # Bright green
                    item.setForeground(QColor(255, 255, 255))  # White text
                elif distance < 1.0:
                    item.setBackground(QColor(144, 238, 144))  # Light green
                elif distance < 2.0:
                    item.setBackground(QColor(255, 255, 100))  # Yellow
                elif distance < 3.0:
                    item.setBackground(QColor(255, 165, 0))    # Orange
                else:
                    item.setBackground(QColor(255, 100, 100))  # Light red
                    item.setForeground(QColor(0, 0, 0))         # Black text
                
                self.distance_table.setItem(i, j, item)
        
        # Resize columns uniformly
        col_width = 70
        for i in range(n):
            self.distance_table.setColumnWidth(i, col_width)
        self.distance_table.setRowHeight(0, 30)
        for i in range(1, n):
            self.distance_table.setRowHeight(i, 28)
        self.distance_table.horizontalHeader().setStretchLastSection(False)


class AnalyticsTab(QWidget):
    """Analytics and statistics."""
    
    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Analytics & Statistics")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Analytics")
        refresh_btn.clicked.connect(self.update_analytics)
        layout.addWidget(refresh_btn)
        
        # Stats text area
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        
        self.setLayout(layout)
        self.update_analytics()
    
    def update_analytics(self):
        """Update analytics display."""
        if not self.app.current_solution:
            self.stats_text.setText("No solution available. Please run the optimizer first.")
            return
        
        sol = self.app.current_solution
        stats = []
        
        stats.append("=" * 60)
        stats.append("OPTIMIZATION SOLUTION ANALYTICS")
        stats.append("=" * 60)
        stats.append("")
        
        stats.append("SUMMARY METRICS:")
        stats.append(f"  Total Travel Time: {sol.total_travel_time:.2f} hours")
        stats.append(f"  Total Service Time: {sol.total_service_time:.2f} hours")
        stats.append(f"  Total Time (Travel + Service): {sol.total_travel_time + sol.total_service_time:.2f} hours")
        stats.append(f"  Objective Value: {sol.objective_value:.3f}")
        stats.append(f"  Solver Status: {sol.solver_status}")
        stats.append(f"  Solve Time: {sol.solve_time:.2f} seconds")
        if sol.gap is not None:
            stats.append(f"  MIP Gap: {sol.gap:.2%}")
        stats.append("")
        
        stats.append("ROUTE STATISTICS:")
        total_tasks = sum(r.tasks_completed for r in sol.routes.values())
        stats.append(f"  Total Tasks Assigned: {total_tasks}")
        stats.append(f"  Number of Inspectors: {len(sol.routes)}")
        stats.append("")
        
        stats.append("INSPECTOR WORKLOAD BREAKDOWN:")
        for ins_id, route_sol in sol.routes.items():
            stats.append(f"\n  {ins_id}:")
            stats.append(f"    - Route: {route_sol.route}")
            stats.append(f"    - Travel Time: {route_sol.travel_time:.2f} h")
            stats.append(f"    - Service Time: {route_sol.service_time:.2f} h")
            stats.append(f"    - Total Time: {route_sol.total_time:.2f} h")
            stats.append(f"    - Tasks Completed: {route_sol.tasks_completed}")
            utilization = (route_sol.total_time / 8.0) * 100 if route_sol.total_time > 0 else 0
            stats.append(f"    - Utilization: {utilization:.1f}%")
        
        stats.append("")
        stats.append("=" * 60)
        
        self.stats_text.setText("\n".join(stats))


class MainApplication(QMainWindow):
    """Main application window with multi-tab interface."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inspection Routing Optimization System")
        self.setGeometry(100, 100, 1400, 900)
        
        # App state
        self.inspectors = []
        self.tasks = []
        self.depot = Depot(x=50, y=50)
        self.use_depot_start = False
        self.current_solution = None
        
        # Load initial data
        self.load_initial_data()
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(DashboardTab(self), "Dashboard")
        self.tabs.addTab(InspectorsTab(self), "Inspectors")
        self.tabs.addTab(TasksTab(self), "Tasks")
        self.tabs.addTab(VisualizationTab(self), "Routes Map")
        self.tabs.addTab(DistancesTab(self), "Distances")
        self.tabs.addTab(AnalyticsTab(self), "Analytics")
        
        self.setCentralWidget(self.tabs)
        
        # Menu bar
        self.create_menu_bar()
        
        # Show
        self.show()
    
    def create_menu_bar(self):
        """Create menu bar with file operations."""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        
        load_action = file_menu.addAction("Load Sample Dataset")
        load_action.triggered.connect(self.load_sample_dataset)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)
    
    def load_initial_data(self):
        """Load initial dataset."""
        self.load_sample_dataset()
    
    def load_sample_dataset(self):
        """Load predefined sample dataset."""
        inspectors, tasks, depot = DatasetGenerator.generate_dataset(
            num_inspectors=3,
            num_tasks=10,
            structured=True
        )
        self.inspectors = list(inspectors)
        self.tasks = list(tasks)
        self.depot = depot
        
        # Refresh tabs if they exist
        if hasattr(self, 'tabs'):
            for i in range(1, 3):  # Inspectors and Tasks tabs
                if hasattr(self.tabs.widget(i), 'refresh_table'):
                    self.tabs.widget(i).refresh_table()
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.information(
            self,
            "About",
            "Inspection Routing Optimization System\n\n"
            "A Gurobi MILP-based application for optimal inspector scheduling.\n\n"
            "Features:\n"
            "• Multi-inspector routing\n"
            "• Skill-based task assignment\n"
            "• Time window constraints\n"
            "• Real-time visualization\n"
            "• Comprehensive analytics\n"
        )


def main():
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)
        window = MainApplication()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
