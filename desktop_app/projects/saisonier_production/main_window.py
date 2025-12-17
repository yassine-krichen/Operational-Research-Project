import os
import sys
import traceback
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# Ensure the repository root (Operational-Research-Project) is on sys.path so
# `saisonierproduction.py` can be imported regardless of how the launcher is run.
CURRENT_DIR = os.path.dirname(__file__)
# climb three levels: .../desktop_app/projects/saisonier_production -> .../Operational-Research-Project
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    # Reuse the full application defined in the repository to preserve all logic,
    # UI and behavior from `saisonierproduction.py`.
    from saisonierproduction import OptimizationApp
except Exception as _err:
    tb = traceback.format_exc()

    # If import fails (missing deps or path issues), provide a clear placeholder
    # widget so the launcher still works and shows the full traceback for debugging.
    class OptimizationApp(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout(self)
            title = QLabel("Unable to load Saisonier Production module")
            title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            err_label = QLabel(tb)
            err_label.setTextInteractionFlags(err_label.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(err_label)


class SaisonierProductionWindow(QMainWindow):
    """Launcher wrapper that embeds the original `OptimizationApp` from
    `saisonierproduction.py` as the central widget. This keeps the full,
    detailed implementation intact while integrating it into the main
    application launcher structure.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimisation de la Production avec Demande Saisonnière")
        self.resize(1200, 720)
        self.setMinimumSize(1000, 600)

        # Instantiate the original app widget and set it as central widget.
        # `OptimizationApp` is a QWidget-based application defined in
        # `saisonierproduction.py` so embedding it preserves all features.
        self.app_widget = OptimizationApp()
        self.setCentralWidget(self.app_widget)
