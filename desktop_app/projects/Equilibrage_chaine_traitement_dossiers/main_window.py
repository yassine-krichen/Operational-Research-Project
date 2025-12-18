"""
Fenêtre principale de l'application
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTabWidget, QTableWidget,
                             QTableWidgetItem, QMessageBox, QProgressBar,
                             QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox,
                             QComboBox, QTextEdit, QFileDialog, QHeaderView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush
from .models.line_balancing import LineBalancingModel
from .models.data_manager import DataManager
from .solver.gurobi_solver import GurobiSolver
from .utils.visualization import VisualizationWidget
import json

class SolverThread(QThread):
    """Thread pour exécuter le solveur sans bloquer l'interface"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, solver):
        super().__init__()
        self.solver = solver
        
    def run(self):
        try:
            self.progress.emit("Construction du modèle...")
            self.solver.build_model()
            
            self.progress.emit("Résolution en cours...")
            success = self.solver.solve(time_limit=300, mip_gap=0.01)
            
            if success and self.solver.solution:
                self.progress.emit("Solution trouvée!")
                self.finished.emit(self.solver.solution)
            else:
                self.error.emit("Aucune solution trouvée dans le temps imparti")
        except Exception as e:
            self.error.emit(f"Erreur: {str(e)}")

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.model = LineBalancingModel()
        self.solver = None
        self.solution = None
        self.solver_thread = None
        
        self.init_ui()
        self.load_example_data()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Équilibrage de Chaîne - Traitement de Dossiers")
        self.setGeometry(100, 100, 1400, 900)
        
        # Appliquer le style moderne
        self.apply_modern_style()
        
        # Widget central
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # En-tête
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Onglets
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        self.tabs.addTab(self.create_data_tab(), "📊 Données")
        self.tabs.addTab(self.create_parameters_tab(), "⚙️ Paramètres")
        self.tabs.addTab(self.create_results_tab(), "📈 Résultats")
        self.tabs.addTab(self.create_visualization_tab(), "📉 Visualisation")
        
        main_layout.addWidget(self.tabs)
        
        # Barre de contrôle
        control_bar = self.create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Barre de statut avec style
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background: white;
                color: #374151;
                font-weight: 600;
                font-size: 12px;
                border-top: 2px solid #e5e7eb;
                padding: 6px 18px;
            }
        """)
        status_bar.showMessage("✓ Prêt à optimiser")
        
    def create_header(self):
        """Crée l'en-tête de l'application"""
        header = QGroupBox()
        header.setObjectName("appHeader")
        header.setStyleSheet("""
            QGroupBox#appHeader {
                background: #2563eb;
                border: none;
                border-radius: 0px;
                padding: 40px 30px;
                margin: 0px;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        title = QLabel("🏭 Équilibrage de Chaîne de Traitement de Dossiers")
        title_font = QFont("Segoe UI", 26, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; letter-spacing: 0.5px;")
        
        subtitle = QLabel("Optimisation par Programmation Linéaire en Nombres Entiers (PLNE)")
        subtitle_font = QFont("Segoe UI", 12)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            background: rgba(255, 255, 255, 0.15);
            border-radius: 25px;
            padding: 10px 24px;
            font-weight: 500;
        """)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        header.setLayout(layout)
        
        return header
        
    def apply_modern_style(self):
        """Applique un style moderne à l'application"""
        self.setStyleSheet("""
            /* Style global avec fond élégant */
            QMainWindow {
                background: #f5f7fa;
            }
            
            QWidget#centralWidget {
                background: #f5f7fa;
            }
            
            /* Onglets épurés et élégants */
            QTabWidget#mainTabs::pane {
                border: none;
                background: white;
                border-radius: 16px;
                margin: 15px;
                padding: 10px;
            }
            
            QTabBar::tab {
                background: transparent;
                color: #6b7280;
                padding: 16px 32px;
                margin-right: 8px;
                margin-top: 8px;
                border: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: 14px;
                font-weight: 600;
                min-width: 140px;
            }
            
            QTabBar::tab:selected {
                background: white;
                color: #2563eb;
                border-bottom: 3px solid #2563eb;
                margin-top: 5px;
            }
            
            QTabBar::tab:hover:!selected {
                background: rgba(37, 99, 235, 0.08);
                color: #2563eb;
            }
            
            /* GroupBox épuré */
            QGroupBox {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 16px;
                margin-top: 20px;
                padding: 25px 20px 20px 20px;
                font-weight: 700;
                font-size: 15px;
                color: #111827;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 20px;
                top: 10px;
                padding: 6px 16px;
                background: #2563eb;
                color: white;
                border-radius: 20px;
                font-size: 13px;
            }
            
            /* Tables épurées */
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                gridline-color: #f3f4f6;
                selection-background-color: rgba(37, 99, 235, 0.1);
                selection-color: #111827;
                padding: 5px;
            }
            
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f3f4f6;
                color: #111827;
            }
            
            QTableWidget::item:selected {
                background: rgba(37, 99, 235, 0.1);
            }
            
            QHeaderView::section {
                background: #2563eb;
                color: white;
                padding: 14px;
                border: none;
                font-weight: 700;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }
            
            QHeaderView::section:first {
                border-top-left-radius: 10px;
            }
            
            QHeaderView::section:last {
                border-top-right-radius: 10px;
            }
            
            QHeaderView::section:hover {
                background: #1d4ed8;
            }
            
            /* Boutons par défaut */
            QPushButton {
                background: white;
                color: #374151;
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background: #f9fafb;
                border-color: #2563eb;
                color: #2563eb;
            }
            
            QPushButton:pressed {
                background: #f3f4f6;
                border-color: #1d4ed8;
            }
            
            /* Inputs épurés */
            QSpinBox, QDoubleSpinBox, QComboBox {
                background: white;
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 12px 14px;
                font-size: 13px;
                min-height: 30px;
                color: #111827;
                selection-background-color: #2563eb;
                selection-color: white;
            }
            
            QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
                border-color: #9ca3af;
            }
            
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 2px solid #2563eb;
                background: white;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 35px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #6b7280;
                margin-right: 10px;
            }
            
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #2563eb;
                border-radius: 10px;
                selection-background-color: rgba(37, 99, 235, 0.1);
                selection-color: #111827;
                padding: 5px;
            }
            
            /* TextEdit épuré */
            QTextEdit {
                background: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 18px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                color: #111827;
                line-height: 1.7;
            }
            
            QTextEdit:focus {
                border-color: #2563eb;
                background: white;
            }
            
            /* Labels avec meilleure typographie */
            QLabel {
                color: #24292e;
                font-size: 13px;
                font-weight: 500;
            }
            
            /* Scrollbar minimaliste */
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(37, 99, 235, 0.2);
                border-radius: 6px;
                min-height: 40px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(37, 99, 235, 0.4);
            }
            
            QScrollBar::handle:vertical:pressed {
                background: rgba(37, 99, 235, 0.6);
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background: transparent;
                height: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: rgba(37, 99, 235, 0.2);
                border-radius: 6px;
                min-width: 40px;
                margin: 2px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: rgba(37, 99, 235, 0.4);
            }
            
            QScrollBar::handle:horizontal:pressed {
                background: rgba(37, 99, 235, 0.6);
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* Tooltips élégants */
            QToolTip {
                background-color: #111827;
                color: white;
                border: 1px solid #2563eb;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 12px;
            }
            
            /* QMessageBox style */
            QMessageBox {
                background-color: white;
            }
            
            QMessageBox QLabel {
                color: #111827;
                font-size: 13px;
            }
            
            QMessageBox QPushButton {
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                min-width: 80px;
            }
            
            QMessageBox QPushButton:hover {
                background: #1d4ed8;
            }
        """)
        
    def create_data_tab(self):
        """Crée l'onglet de saisie des données"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Section tâches
        tasks_group = QGroupBox("Tâches")
        tasks_layout = QVBoxLayout()
        
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Durée (min)", "Complexité", "Priorité", "Compétences"
        ])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tasks_table.verticalHeader().setDefaultSectionSize(35)
        self.tasks_table.setMinimumHeight(200)
        
        # Boutons avant le tableau
        btn_layout = QHBoxLayout()
        btn_add_task = QPushButton("➕ Ajouter tâche")
        btn_add_task.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #059669;
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        btn_add_task.clicked.connect(self.add_task_row)
        
        btn_remove_task = QPushButton("➖ Supprimer tâche")
        btn_remove_task.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
            QPushButton:pressed {
                background: #b91c1c;
            }
        """)
        btn_remove_task.clicked.connect(self.remove_task_row)
        btn_layout.addWidget(btn_add_task)
        btn_layout.addWidget(btn_remove_task)
        btn_layout.addStretch()
        
        tasks_layout.addLayout(btn_layout)
        tasks_layout.addWidget(self.tasks_table)
        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)
        
        # Section précédences
        prec_group = QGroupBox("Contraintes de précédence")
        prec_layout = QVBoxLayout()
        
        # Boutons avant le tableau
        btn_prec_layout = QHBoxLayout()
        btn_add_prec = QPushButton("➕ Ajouter précédence")
        btn_add_prec.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #059669;
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        btn_add_prec.clicked.connect(self.add_precedence_row)
        
        btn_remove_prec = QPushButton("➖ Supprimer précédence")
        btn_remove_prec.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
            QPushButton:pressed {
                background: #b91c1c;
            }
        """)
        btn_remove_prec.clicked.connect(self.remove_precedence_row)
        btn_prec_layout.addWidget(btn_add_prec)
        btn_prec_layout.addWidget(btn_remove_prec)
        btn_prec_layout.addStretch()
        
        prec_layout.addLayout(btn_prec_layout)
        
        self.precedences_table = QTableWidget()
        self.precedences_table.setColumnCount(2)
        self.precedences_table.setHorizontalHeaderLabels(["Tâche avant", "Tâche après"])
        self.precedences_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.precedences_table.verticalHeader().setDefaultSectionSize(35)
        self.precedences_table.setMinimumHeight(150)
        
        prec_layout.addWidget(self.precedences_table)
        prec_group.setLayout(prec_layout)
        layout.addWidget(prec_group)
        
        return tab
        
    def create_parameters_tab(self):
        """Crée l'onglet des paramètres"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Paramètres d'optimisation
        opt_group = QGroupBox("Paramètres d'optimisation")
        opt_layout = QGridLayout()
        
        opt_layout.addWidget(QLabel("Mode d'optimisation:"), 0, 0)
        self.opt_mode_combo = QComboBox()
        self.opt_mode_combo.addItems([
            "Minimiser le nombre de postes",
            "Minimiser le temps de cycle"
        ])
        opt_layout.addWidget(self.opt_mode_combo, 0, 1)
        
        opt_layout.addWidget(QLabel("Temps de cycle cible (min):"), 1, 0)
        self.cycle_time_spin = QDoubleSpinBox()
        self.cycle_time_spin.setRange(1, 1000)
        self.cycle_time_spin.setValue(60)
        self.cycle_time_spin.setSuffix(" min")
        opt_layout.addWidget(self.cycle_time_spin, 1, 1)
        
        opt_layout.addWidget(QLabel("Nombre max de postes:"), 2, 0)
        self.max_stations_spin = QSpinBox()
        self.max_stations_spin.setRange(1, 50)
        self.max_stations_spin.setValue(10)
        opt_layout.addWidget(self.max_stations_spin, 2, 1)
        
        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)
        
        # Paramètres du solveur
        solver_group = QGroupBox("Paramètres du solveur Gurobi")
        solver_layout = QGridLayout()
        
        solver_layout.addWidget(QLabel("Temps limite (secondes):"), 0, 0)
        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setRange(10, 3600)
        self.time_limit_spin.setValue(300)
        self.time_limit_spin.setSuffix(" s")
        solver_layout.addWidget(self.time_limit_spin, 0, 1)
        
        solver_layout.addWidget(QLabel("Gap MIP (%):"), 1, 0)
        self.mip_gap_spin = QDoubleSpinBox()
        self.mip_gap_spin.setRange(0.01, 10)
        self.mip_gap_spin.setValue(1.0)
        self.mip_gap_spin.setSingleStep(0.1)
        self.mip_gap_spin.setSuffix(" %")
        solver_layout.addWidget(self.mip_gap_spin, 1, 1)
        
        solver_group.setLayout(solver_layout)
        layout.addWidget(solver_group)
        
        layout.addStretch()
        
        return tab
        
    def create_results_tab(self):
        """Crée l'onglet des résultats"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Résumé de la solution
        summary_group = QGroupBox("Résumé de la solution")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(270)
        self.summary_text.setText("Aucune solution disponible. Cliquez sur 'RÉSOUDRE' pour optimiser.")
        self.summary_text.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                color: #111827;
                padding: 22px;
                background: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 14px;
                font-family: 'Consolas', 'Courier New', monospace;
                line-height: 1.7;
            }
        """)
        summary_layout.addWidget(self.summary_text)
        
        # Boutons d'export
        export_layout = QHBoxLayout()
        btn_export_excel = QPushButton("📊 Exporter vers Excel")
        btn_export_excel.setStyleSheet("""
            QPushButton {
                background: #0891b2;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 13px 26px;
                font-weight: 600;
                font-size: 13px;
                min-width: 180px;
            }
            QPushButton:hover {
                background: #0e7490;
            }
            QPushButton:pressed {
                background: #155e75;
            }
        """)
        btn_export_excel.clicked.connect(self.export_to_excel)
        
        btn_export_json = QPushButton("💾 Exporter JSON")
        btn_export_json.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 13px 26px;
                font-weight: 600;
                font-size: 13px;
                min-width: 180px;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
            QPushButton:pressed {
                background: #6d28d9;
            }
        """)
        btn_export_json.clicked.connect(self.export_to_json)
        export_layout.addWidget(btn_export_excel)
        export_layout.addWidget(btn_export_json)
        export_layout.addStretch()
        
        summary_layout.addLayout(export_layout)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Affectations
        assign_group = QGroupBox("Affectation des tâches aux postes")
        assign_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Poste", "Tâches", "Temps total (min)", "Temps inactif (min)", "Efficacité (%)"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.verticalHeader().setDefaultSectionSize(35)
        self.results_table.setMinimumHeight(200)
        
        assign_layout.addWidget(self.results_table)
        assign_group.setLayout(assign_layout)
        layout.addWidget(assign_group)
        
        # Boutons d'export
        export_layout = QHBoxLayout()
        btn_export_excel = QPushButton("📊 Exporter vers Excel")
        btn_export_excel.clicked.connect(self.export_to_excel)
        btn_export_json = QPushButton("💾 Exporter JSON")
        btn_export_json.clicked.connect(self.export_to_json)
        export_layout.addWidget(btn_export_excel)
        export_layout.addWidget(btn_export_json)
        export_layout.addStretch()
        
        layout.addLayout(export_layout)
        
        return tab
        
    def create_visualization_tab(self):
        """Crée l'onglet de visualisation"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Boutons de sélection de visualisation
        btn_layout = QHBoxLayout()
        
        viz_btn_style = """
            QPushButton {
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 13px 22px;
                font-weight: 600;
                font-size: 13px;
                min-width: 160px;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            QPushButton:pressed {
                background: #1e40af;
            }
        """
        
        btn_gantt = QPushButton("📊 Diagramme de Gantt")
        btn_gantt.setStyleSheet(viz_btn_style)
        btn_gantt.clicked.connect(lambda: self.show_visualization('gantt'))
        
        btn_efficiency = QPushButton("📈 Efficacité")
        btn_efficiency.setStyleSheet(viz_btn_style)
        btn_efficiency.clicked.connect(lambda: self.show_visualization('efficiency'))
        
        btn_workload = QPushButton("⚖️ Charge de travail")
        btn_workload.setStyleSheet(viz_btn_style)
        btn_workload.clicked.connect(lambda: self.show_visualization('workload'))
        
        btn_summary = QPushButton("📑 Résumé")
        btn_summary.setStyleSheet(viz_btn_style)
        btn_summary.clicked.connect(lambda: self.show_visualization('summary'))
        
        btn_layout.addWidget(btn_gantt)
        btn_layout.addWidget(btn_efficiency)
        btn_layout.addWidget(btn_workload)
        btn_layout.addWidget(btn_summary)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Widget de visualisation
        self.viz_widget = VisualizationWidget(self, width=10, height=6)
        layout.addWidget(self.viz_widget)
        
        return tab
        btn_efficiency = QPushButton("📈 Efficacité")
        btn_efficiency.clicked.connect(lambda: self.show_visualization('efficiency'))
    def create_control_bar(self):
        """Crée la barre de contrôle"""
        control_widget = QWidget()
        control_widget.setObjectName("controlBar")
        control_widget.setStyleSheet("""
            QWidget#controlBar {
                background: white;
                border-top: 2px solid #e5e7eb;
                padding: 20px 30px;
            }
        """)
        
        layout = QHBoxLayout(control_widget)
        layout.setSpacing(12)
        
        # Style pour les boutons secondaires
        btn_secondary_style = """
            QPushButton {
                background: white;
                color: #374151;
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 13px 24px;
                font-size: 13px;
                font-weight: 600;
                min-width: 160px;
            }
            QPushButton:hover {
                background: #f9fafb;
                border-color: #2563eb;
                color: #2563eb;
            }
            QPushButton:pressed {
                background: #f3f4f6;
                border-color: #1d4ed8;
            }
        """
        
        # Boutons
        self.btn_load = QPushButton("📁 Charger données")
        self.btn_load.setStyleSheet(btn_secondary_style)
        self.btn_load.clicked.connect(self.load_data)
        
        self.btn_save = QPushButton("💾 Sauvegarder")
        self.btn_save.setStyleSheet(btn_secondary_style)
        self.btn_save.clicked.connect(self.save_data)
        
        self.btn_example = QPushButton("📋 Charger exemple")
        self.btn_example.setStyleSheet(btn_secondary_style)
        self.btn_example.clicked.connect(self.load_example_data)
        
        self.btn_solve = QPushButton("🚀 RÉSOUDRE")
        self.btn_solve.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                font-weight: 700;
                font-size: 16px;
                padding: 16px 45px;
                border: none;
                border-radius: 12px;
                min-width: 220px;
                letter-spacing: 1.5px;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            QPushButton:pressed {
                background: #1e40af;
            }
            QPushButton:disabled {
                background: #9ca3af;
            }
        """)
        self.btn_solve.clicked.connect(self.solve_problem)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(True)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #d1d5db;
                border-radius: 12px;
                text-align: center;
                background: white;
                min-width: 300px;
                max-height: 26px;
                font-weight: 600;
                color: white;
            }
            QProgressBar::chunk {
                background: #2563eb;
                border-radius: 10px;
            }
        """)
        
        layout.addWidget(self.btn_load)
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_example)
        layout.addStretch()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.btn_solve)
        
        return control_widget
        
    def add_task_row(self):
        """Ajoute une ligne dans le tableau des tâches"""
        row = self.tasks_table.rowCount()
        self.tasks_table.insertRow(row)
        self.tasks_table.setItem(row, 0, QTableWidgetItem(f"T{row+1}"))
        self.tasks_table.setItem(row, 1, QTableWidgetItem(f"Tâche {row+1}"))
        self.tasks_table.setItem(row, 2, QTableWidgetItem("10"))
        self.tasks_table.setItem(row, 3, QTableWidgetItem("1"))
        self.tasks_table.setItem(row, 4, QTableWidgetItem("1"))
        self.tasks_table.setItem(row, 5, QTableWidgetItem(""))
        
    def remove_task_row(self):
        """Supprime une ligne du tableau des tâches"""
        current_row = self.tasks_table.currentRow()
        if current_row >= 0:
            self.tasks_table.removeRow(current_row)
            
    def add_precedence_row(self):
        """Ajoute une ligne dans le tableau des précédences"""
        row = self.precedences_table.rowCount()
        self.precedences_table.insertRow(row)
        self.precedences_table.setItem(row, 0, QTableWidgetItem(""))
        self.precedences_table.setItem(row, 1, QTableWidgetItem(""))
        
    def remove_precedence_row(self):
        """Supprime une ligne du tableau des précédences"""
        current_row = self.precedences_table.currentRow()
        if current_row >= 0:
            self.precedences_table.removeRow(current_row)
            
    def load_example_data(self):
        """Charge les données d'exemple"""
        data = DataManager.create_example_data()
        self.populate_ui_from_data(data)
        self.statusBar().showMessage("Données d'exemple chargées")
        
    def populate_ui_from_data(self, data):
        """Remplit l'interface avec les données"""
        # Tâches
        self.tasks_table.setRowCount(0)
        for task in data.get('tasks', []):
            row = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row)
            self.tasks_table.setItem(row, 0, QTableWidgetItem(task['id']))
            self.tasks_table.setItem(row, 1, QTableWidgetItem(task['name']))
            self.tasks_table.setItem(row, 2, QTableWidgetItem(str(task['duration'])))
            self.tasks_table.setItem(row, 3, QTableWidgetItem(str(task.get('complexity', 1))))
            self.tasks_table.setItem(row, 4, QTableWidgetItem(str(task.get('priority', 1))))
            self.tasks_table.setItem(row, 5, QTableWidgetItem(','.join(task.get('skills', []))))
            
        # Précédences
        self.precedences_table.setRowCount(0)
        for prec in data.get('precedences', []):
            row = self.precedences_table.rowCount()
            self.precedences_table.insertRow(row)
            self.precedences_table.setItem(row, 0, QTableWidgetItem(prec[0]))
            self.precedences_table.setItem(row, 1, QTableWidgetItem(prec[1]))
            
        # Paramètres
        if 'cycle_time' in data:
            self.cycle_time_spin.setValue(data['cycle_time'])
        if 'max_stations' in data:
            self.max_stations_spin.setValue(data['max_stations'])
            
    def build_model_from_ui(self):
        """Construit le modèle à partir des données de l'interface"""
        self.model = LineBalancingModel()
        
        # Ajouter les tâches
        for row in range(self.tasks_table.rowCount()):
            task_id = self.tasks_table.item(row, 0).text()
            duration = float(self.tasks_table.item(row, 2).text())
            complexity = int(self.tasks_table.item(row, 3).text())
            priority = int(self.tasks_table.item(row, 4).text())
            skills_text = self.tasks_table.item(row, 5).text()
            skills = [s.strip() for s in skills_text.split(',') if s.strip()]
            
            self.model.add_task(task_id, duration, complexity, priority, skills)
            
        # Ajouter les précédences
        for row in range(self.precedences_table.rowCount()):
            before = self.precedences_table.item(row, 0).text()
            after = self.precedences_table.item(row, 1).text()
            if before and after:
                self.model.add_precedence(before, after)
                
        # Paramètres
        self.model.cycle_time = self.cycle_time_spin.value()
        self.model.num_stations = self.max_stations_spin.value()
        
        if self.opt_mode_combo.currentIndex() == 0:
            self.model.optimization_mode = "minimize_stations"
        else:
            self.model.optimization_mode = "minimize_cycle_time"
        
        # Initialiser les compétences des postes (toutes disponibles par défaut)
        all_skills = set()
        for task in self.model.tasks:
            all_skills.update(self.model.skills_required.get(task, []))
        
        # Affecter toutes les compétences à tous les postes par défaut
        for j in range(self.model.num_stations):
            self.model.station_skills[j] = list(all_skills)
            
        # Valider
        errors = self.model.validate_data()
        if errors:
            QMessageBox.warning(self, "Erreurs de validation", "\n".join(errors))
            return False
            
        return True
        
    def solve_problem(self):
        """Lance la résolution"""
        if not self.build_model_from_ui():
            return
            
        # Créer le solveur
        self.solver = GurobiSolver(self.model)
        
        # Lancer dans un thread
        self.solver_thread = SolverThread(self.solver)
        self.solver_thread.finished.connect(self.on_solution_found)
        self.solver_thread.error.connect(self.on_solver_error)
        self.solver_thread.progress.connect(self.on_solver_progress)
        
        # Désactiver le bouton
        self.btn_solve.setEnabled(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        
        self.solver_thread.start()
        
    def on_solution_found(self, solution):
        """Callback quand une solution est trouvée"""
        self.solution = solution
        self.display_solution(solution)
        
        self.btn_solve.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.statusBar().showMessage("Solution trouvée!")
        
        QMessageBox.information(self, "Succès", 
                               f"Solution trouvée!\n\n"
                               f"Nombre de postes: {int(solution['num_stations_used'])}\n"
                               f"Temps de cycle: {solution['cycle_time']:.1f} min\n"
                               f"Efficacité: {solution['summary']['overall_efficiency']:.1f}%")
        
        # Basculer vers l'onglet résultats
        self.tabs.setCurrentIndex(2)
        
    def on_solver_error(self, error_msg):
        """Callback en cas d'erreur"""
        self.btn_solve.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.statusBar().showMessage("Erreur")
        QMessageBox.critical(self, "Erreur", error_msg)
        
    def on_solver_progress(self, message):
        """Callback pour les messages de progression"""
        self.statusBar().showMessage(message)
        
    def display_solution(self, solution):
        """Affiche la solution dans l'interface"""
        # Résumé
        summary_text = f"""
RÉSULTAT DE L'OPTIMISATION

Statut: {solution['status'].upper()}
Temps de résolution: {solution['solve_time']:.2f} secondes
Gap MIP: {solution['mip_gap']*100:.2f}%

SOLUTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nombre de postes utilisés: {int(solution['num_stations_used'])}
Temps de cycle: {solution['cycle_time']:.1f} minutes

EFFICACITÉ:
Temps de traitement total: {solution['summary']['total_processing_time']:.1f} min
Temps disponible total: {solution['summary']['total_available_time']:.1f} min
Efficacité globale: {solution['summary']['overall_efficiency']:.1f}%
Perte d'équilibrage: {solution['summary']['balance_delay']:.1f}%
        """
        self.summary_text.setText(summary_text)
        
        # Tableau des affectations
        self.results_table.setRowCount(0)
        for assignment in solution['assignments']:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            # Poste
            self.results_table.setItem(row, 0, QTableWidgetItem(f"Poste {assignment['station']}"))
            
            # Tâches
            tasks_str = ", ".join([t['task_id'] for t in assignment['tasks']])
            self.results_table.setItem(row, 1, QTableWidgetItem(tasks_str))
            
            # Temps total
            item = QTableWidgetItem(f"{assignment['total_time']:.1f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 2, item)
            
            # Temps inactif
            item = QTableWidgetItem(f"{assignment['idle_time']:.1f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 3, item)
            
            # Efficacité
            efficiency = assignment['efficiency']
            item = QTableWidgetItem(f"{efficiency:.1f}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Couleur selon efficacité
            if efficiency >= 90:
                item.setBackground(QBrush(QColor(144, 238, 144)))  # Vert clair
            elif efficiency >= 75:
                item.setBackground(QBrush(QColor(255, 215, 0)))  # Jaune
            else:
                item.setBackground(QBrush(QColor(255, 182, 193)))  # Rouge clair
                
            self.results_table.setItem(row, 4, item)
            
    def show_visualization(self, viz_type):
        """Affiche une visualisation"""
        if not self.solution:
            QMessageBox.warning(self, "Attention", "Aucune solution à visualiser. Veuillez d'abord résoudre le problème.")
            return
            
        if viz_type == 'gantt':
            self.viz_widget.plot_gantt_chart(self.solution)
        elif viz_type == 'efficiency':
            self.viz_widget.plot_efficiency_bars(self.solution)
        elif viz_type == 'workload':
            self.viz_widget.plot_workload_distribution(self.solution)
        elif viz_type == 'summary':
            self.viz_widget.plot_summary_statistics(self.solution)
            
    def load_data(self):
        """Charge des données depuis un fichier"""
        filename, _ = QFileDialog.getOpenFileName(self, "Charger données", "", "JSON Files (*.json)")
        if filename:
            try:
                data = DataManager.load_from_json(filename)
                self.populate_ui_from_data(data)
                self.statusBar().showMessage(f"Données chargées depuis {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur de chargement: {str(e)}")
                
    def save_data(self):
        """Sauvegarde les données dans un fichier"""
        filename, _ = QFileDialog.getSaveFileName(self, "Sauvegarder données", "", "JSON Files (*.json)")
        if filename:
            try:
                data = self.collect_data_from_ui()
                DataManager.save_to_json(data, filename)
                self.statusBar().showMessage(f"Données sauvegardées dans {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur de sauvegarde: {str(e)}")
                
    def collect_data_from_ui(self):
        """Collecte les données depuis l'interface"""
        data = {
            'tasks': [],
            'precedences': [],
            'cycle_time': self.cycle_time_spin.value(),
            'max_stations': self.max_stations_spin.value()
        }
        
        # Tâches
        for row in range(self.tasks_table.rowCount()):
            task = {
                'id': self.tasks_table.item(row, 0).text(),
                'name': self.tasks_table.item(row, 1).text(),
                'duration': float(self.tasks_table.item(row, 2).text()),
                'complexity': int(self.tasks_table.item(row, 3).text()),
                'priority': int(self.tasks_table.item(row, 4).text()),
                'skills': [s.strip() for s in self.tasks_table.item(row, 5).text().split(',') if s.strip()]
            }
            data['tasks'].append(task)
            
        # Précédences
        for row in range(self.precedences_table.rowCount()):
            prec = [
                self.precedences_table.item(row, 0).text(),
                self.precedences_table.item(row, 1).text()
            ]
            if prec[0] and prec[1]:
                data['precedences'].append(prec)
                
        return data
        
    def export_to_excel(self):
        """Exporte la solution vers Excel"""
        if not self.solution:
            QMessageBox.warning(self, "Attention", "Aucune solution à exporter")
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, "Exporter vers Excel", "", "Excel Files (*.xlsx)")
        if filename:
            try:
                DataManager.export_solution_to_excel(self.solution, filename)
                self.statusBar().showMessage(f"Solution exportée vers {filename}")
                QMessageBox.information(self, "Succès", "Solution exportée avec succès!")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur d'export: {str(e)}")
                
    def export_to_json(self):
        """Exporte la solution vers JSON"""
        if not self.solution:
            QMessageBox.warning(self, "Attention", "Aucune solution à exporter")
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, "Exporter vers JSON", "", "JSON Files (*.json)")
        if filename:
            try:
                DataManager.save_to_json(self.solution, filename)
                self.statusBar().showMessage(f"Solution exportée vers {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur d'export: {str(e)}")
