import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Add project root to sys.path to allow imports from sibling directories
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Import project modules
from desktop_app.projects.hospital_scheduler_gui.main_window import HospitalSchedulerWindow
from desktop_app.projects.saisonier_production.main_window import SaisonierProductionWindow
from desktop_app.projects.Equilibrage_chaine_traitement_dossiers.main_window import MainWindow as EquilibrageWindow


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OR Project Group Launcher")
        self.resize(800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QPushButton {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                padding: 20px;
                text-align: left;
                font-size: 16px;
                color: #1f2937;
            }
            QPushButton:hover {
                background-color: #f9fafb;
                border-color: #3b82f6;
            }
            QPushButton:pressed {
                background-color: #eff6ff;
            }
            QLabel#Title {
                font-size: 28px;
                font-weight: bold;
                color: #111827;
                margin-bottom: 20px;
            }
            QLabel#Subtitle {
                font-size: 16px;
                color: #6b7280;
                margin-bottom: 40px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("Operations Research Project")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Select a module to launch")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        # Grid for Projects
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        # Project 1: Hospital Scheduler (Your Project)
        self.btn_project1 = QPushButton("🏥  Hospital Staff Scheduler\n\nOptimized nurse rostering using Gurobi")
        self.btn_project1.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_project1.clicked.connect(self.launch_hospital_scheduler)
        self.btn_project1.setFixedSize(300, 150)
        
        # Project 2: Optimisation de la Production avec Demande Saisonnière
        self.btn_project2 = QPushButton("📦  Optimisation de la Production avec Demande Saisonnière")
        self.btn_project2.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_project2.clicked.connect(self.launch_saisonier_production)
        self.btn_project2.setFixedSize(300, 150)

        # Project 3: Équilibrage de Chaîne
        self.btn_project3 = QPushButton("🏭  Équilibrage de Chaîne de Traitement\n\nOptimisation PLNE avec Gurobi")
        self.btn_project3.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_project3.clicked.connect(self.launch_equilibrage)
        self.btn_project3.setFixedSize(300, 150)

        # Project 4: Placeholder
        self.btn_project4 = QPushButton("⚡  Project 4\n\nComing Soon...")
        self.btn_project4.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_project4.setEnabled(False)
        self.btn_project4.setFixedSize(300, 150)

        grid_layout.addWidget(self.btn_project1, 0, 0)
        grid_layout.addWidget(self.btn_project2, 0, 1)
        grid_layout.addWidget(self.btn_project3, 1, 0)
        grid_layout.addWidget(self.btn_project4, 1, 1)

        main_layout.addLayout(grid_layout)

    def launch_hospital_scheduler(self):
        self.hospital_window = HospitalSchedulerWindow()
        self.hospital_window.show()
        # Optional: Hide launcher or keep it open
        # self.hide()

    def launch_saisonier_production(self):
        self.saisonier_window = SaisonierProductionWindow()
        self.saisonier_window.show()

    def launch_equilibrage(self):
        self.equilibrage_window = EquilibrageWindow()
        self.equilibrage_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = LauncherWindow()
    window.show()
    
    sys.exit(app.exec())
