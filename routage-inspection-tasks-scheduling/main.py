# main.py

import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
from optimizer import solve_routing
from dataset_generator import DatasetGenerator
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

UI_FILE = "frontend.ui"

# Load dataset on startup
inspectors, tasks, depot = DatasetGenerator.generate_dataset(
    num_inspectors=3,
    num_tasks=10,
    structured=True
)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_FILE, self)

        # Buttons
        self.btnLoadData.clicked.connect(self.load_data)
        self.btnSolve.clicked.connect(self.solve)
        self.btnShowRoutes.clicked.connect(self.show_routes)

        # Status label
        self.lblStatus.setText("Status: idle")

        # Table for results
        self.tableAssignments.setColumnCount(3)
        self.tableAssignments.setHorizontalHeaderLabels(["Inspector", "Route", "Travel Time (h)"])

        # Prepare matplotlib canvas in the QGraphicsView
        self.figure = plt.figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        self.mapView.setScene(QtWidgets.QGraphicsScene())
        self.mapView.scene().addWidget(self.canvas)

    def load_data(self):
        # Displays a message and status
        num_sites = len(tasks)
        num_ins = len(inspectors)
        QMessageBox.information(self, "Data loaded",
                                f"Loaded {num_sites} inspection sites and {num_ins} inspectors.")
        self.lblStatus.setText("Status: data loaded")

    def solve(self):
        self.lblStatus.setText("Status: solving...")
        QtWidgets.QApplication.processEvents()

        try:
            sol = solve_routing(inspectors, tasks, depot, time_limit=60)
        except Exception as e:
            QMessageBox.critical(self, "Solver error", str(e))
            self.lblStatus.setText("Status: error")
            return

        self.solution = sol
        obj = sol.objective_value
        self.lblStatus.setText(f"Status: solved — objective = {obj:.3f}")
        self.populate_table()

    def populate_table(self):
        sol = self.solution
        routes = sol.routes

        self.tableAssignments.setRowCount(len(inspectors))
        for i, ins in enumerate(inspectors):
            ins_id = ins.id
            route_sol = routes[ins_id]
            travel = route_sol.travel_time
            self.tableAssignments.setItem(i, 0, QTableWidgetItem(ins_id))
            self.tableAssignments.setItem(i, 1, QTableWidgetItem(str(route_sol.route)))
            self.tableAssignments.setItem(i, 2, QTableWidgetItem(f"{travel:.2f}"))

    def show_routes(self):
        if not hasattr(self, "solution"):
            QMessageBox.warning(self, "No solution", "You must run solve first.")
            return

        routes = self.solution.routes

        # Plot nodes
        xs = [task.x for task in tasks]
        ys = [task.y for task in tasks]

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Plot depot
        ax.scatter(depot.x, depot.y, c="red", s=100, label="Depot")

        # Plot sites
        for task in tasks:
            ax.scatter(task.x, task.y, c="blue", s=50)
            ax.text(task.x + 0.5, task.y + 0.5, str(task.id), fontsize=9)

        # Plot each inspector route
        colors = ["green", "purple", "orange", "cyan", "magenta"]
        for idx, ins in enumerate(inspectors):
            ins_id = ins.id
            route_sol = routes[ins_id]
            route = route_sol.route
            if len(route) == 0:
                continue

            # Build full route with coordinates
            route_coords = [(depot.x, depot.y)]  # start at depot
            for task_id in route:
                if task_id == 0:
                    continue
                # find task
                task = next(t for t in tasks if t.id == task_id)
                route_coords.append((task.x, task.y))
            route_coords.append((depot.x, depot.y))  # return to depot

            rx = [coord[0] for coord in route_coords]
            ry = [coord[1] for coord in route_coords]

            ax.plot(rx, ry, linestyle="-", marker="o", color=colors[idx % len(colors)],
                    label=f"{ins_id}")

        ax.legend()
        ax.set_title("Inspector Routes")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

        self.canvas.draw()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
