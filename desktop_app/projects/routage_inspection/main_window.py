import os
import sys
import traceback
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# Ensure the repository root is on sys.path so the routage-inspection-tasks-scheduling
# module can be imported regardless of how the launcher is run.
CURRENT_DIR = os.path.dirname(__file__)
# climb three levels: .../desktop_app/projects/routage_inspection -> .../Operational-Research-Project
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Add the routage-inspection-tasks-scheduling directory to path
ROUTAGE_DIR = os.path.join(PROJECT_ROOT, 'routage-inspection-tasks-scheduling')
if ROUTAGE_DIR not in sys.path:
    sys.path.insert(0, ROUTAGE_DIR)

try:
    # Import the comprehensive app from app.py (the advanced multi-tab version)
    from app import MainApplication
except Exception as _err:
    tb = traceback.format_exc()

    # If import fails (missing deps or path issues), provide a clear placeholder
    # widget so the launcher still works and shows the full traceback for debugging.
    class MainApplication(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout(self)
            title = QLabel("Unable to load Routage Inspection module")
            title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            err_label = QLabel(tb)
            err_label.setTextInteractionFlags(err_label.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(err_label)


class RoutageInspectionWindow(QMainWindow):
    """Launcher wrapper that embeds the original `MainApplication` from
    `routage-inspection-tasks-scheduling/app.py` as the central widget. This keeps 
    the full, detailed implementation intact while integrating it into the main
    application launcher structure.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Routage & Inspection Tasks Scheduling")
        self.resize(1400, 800)
        self.setMinimumSize(1200, 700)

        # Instantiate the original app. Since MainApplication is already a QMainWindow,
        # we simply create it and it will show itself.
        # Note: MainApplication calls self.show() in its __init__, so we store the reference
        # but don't need to do anything else.
        self.app_widget = None
        
    def show(self):
        """Override show to create and display the embedded app."""
        super().show()
        # Create and show the MainApplication (it's already a standalone QMainWindow)
        if self.app_widget is None:
            self.app_widget = MainApplication()
        # The MainApplication already calls show() in its __init__
        # so we don't need to call it again
        # Just hide this wrapper window since we're showing the actual app
        self.hide()
