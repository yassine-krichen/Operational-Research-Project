# How to Add Your Project to the Launcher

Follow these steps to integrate your module into the main application launcher.

## 1. Create Your Project Folder

Navigate to `desktop_app/projects/` and create a new folder for your project.
Example: `desktop_app/projects/transport_optimization/`

## 2. Create Your Main Window

Inside your project folder, create a file (e.g., `main_window.py`) that defines your main application window. It should inherit from `QMainWindow` or `QWidget`.

**Template (`desktop_app/projects/transport_optimization/main_window.py`):**

```python
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget

class TransportWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transport Optimization")
        self.resize(800, 600)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add your UI components here
        label = QLabel("Welcome to Transport Optimization Module")
        layout.addWidget(label)
```

## 3. Register in the Launcher

Open `desktop_app/main.py` and follow these steps:

### A. Import your class

Add the import statement at the top of the file with the other imports:

```python
# ... existing imports ...
from desktop_app.projects.hospital_scheduler_gui.main_window import HospitalSchedulerWindow
# Add your import here:
from desktop_app.projects.transport_optimization.main_window import TransportWindow
```

### B. Update the Button

Find the placeholder buttons in the `__init__` method (e.g., `self.btn_project2`) and update it:

```python
        # Project 2: Transport Optimization
        self.btn_project2 = QPushButton("🚚  Transport Optimization\n\nRoute planning and vehicle scheduling")
        self.btn_project2.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_project2.clicked.connect(self.launch_transport_project) # Connect to your launcher function
        self.btn_project2.setFixedSize(300, 150)
        # Remove or comment out this line to enable the button:
        # self.btn_project2.setEnabled(False)
```

### C. Add the Launcher Method

Add a new method to the `LauncherWindow` class to handle opening your window:

```python
    # ... existing methods ...

    def launch_hospital_scheduler(self):
        self.hospital_window = HospitalSchedulerWindow()
        self.hospital_window.show()

    # Add your method here:
    def launch_transport_project(self):
        self.transport_window = TransportWindow()
        self.transport_window.show()
```

## 4. Run the Application

Run `desktop_app/main.py` to test your integration.

```bash
python desktop_app/main.py
```
