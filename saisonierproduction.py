import sys
import traceback

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QSpinBox, QComboBox, QLabel, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox,
    QTabWidget, QGridLayout, QSizePolicy, QScrollArea, QSplitter
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import gurobipy as grb


class OptimizationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Product Production Optimization • Planner")
        self.setGeometry(100, 100, 1200, 720)
        self.setMinimumSize(1000, 600)

        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                padding: 3px;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                padding: 6px;
                border-radius: 4px;
                color: #ffffff;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 2px solid #00bcd4;
            }
            QPushButton {
                background-color: #00bcd4;
                color: white;
                border: none;
                padding: 8px 14px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00acc1;
            }
            QPushButton:pressed {
                background-color: #008c9e;
            }
            QTabWidget::pane {
                border: 1px solid #333333;
                background: #1e1e1e;
            }
            QTabBar::tab {
                background: #2d2d2d;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #00bcd4;
                color: white;
            }
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333333;
                alternate-background-color: #252525;
                selection-background-color: #00bcd4;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 6px;
                border: none;
                font-weight: bold;
                color: #e0e0e0;
            }
        """)

        self.font_title = QFont("Segoe UI", 13, QFont.Weight.Bold)

        self.months_full = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        self._build_main_layout()
        self._build_left_panel()
        self._build_right_panel()

        self.results_widget = None
        self.current_month_idx = 0

    # ---------- Main layout with splitter ---------- #
    def _build_main_layout(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(4)

        # left and right placeholders
        self.left_container = QWidget()
        self.right_container = QWidget()

        splitter.addWidget(self.left_container)
        splitter.addWidget(self.right_container)

        splitter.setStretchFactor(0, 0)   # left fixed-ish
        splitter.setStretchFactor(1, 1)   # right grows

        splitter.setSizes([350, 850])

        main_layout.addWidget(splitter)

    # ---------- Left: parameters + demand (scrollable) ---------- #
    def _build_left_panel(self):
        left_layout_outer = QVBoxLayout(self.left_container)
        left_layout_outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(6, 6, 6, 6)
        scroll_layout.setSpacing(8)

        title = QLabel("Inputs")
        title.setFont(self.font_title)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(title)

        # form for global parameters
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(4)

        self.inputs = {}
        defaults = {
            "Number of Seasons": "4",
            "Worker Salary": "1500",
            "Overtime Hourly Rate": "13",
            "Material Cost per Unit": "15",
            "Recruitment Cost": "1600",
            "Layoff Cost": "2000",
            "Storage Cost per Unit": "3",
            "Max Overtime Hours": "20",
            "Initial Stock": "500",
            "Desired Final Stock": "0",
            "Initial Workers": "100",
            "Work Hours per Unit": "4",
            "Regular Hours per Worker": "160"
        }

        # number of seasons as spinbox (better than lineedit)
        self.num_seasons_spin = QSpinBox()
        self.num_seasons_spin.setRange(1, 4)
        self.num_seasons_spin.setValue(int(defaults["Number of Seasons"]))
        form.addRow("Number of Seasons:", self.num_seasons_spin)

        for k, v in defaults.items():
            if k == "Number of Seasons":
                continue
            le = QLineEdit(v)
            le.setMinimumWidth(80)
            self.inputs[k] = le
            form.addRow(k + ":", le)

        scroll_layout.addLayout(form)

        # seasonal demand block
        demand_title = QLabel("Seasonal Demand (units)")
        demand_title.setFont(self.font_title)
        scroll_layout.addWidget(demand_title)

        self.demand_container = QWidget()
        self.demand_layout = QVBoxLayout(self.demand_container)
        self.demand_layout.setContentsMargins(0, 0, 0, 0)
        self.demand_layout.setSpacing(4)
        scroll_layout.addWidget(self.demand_container)

        # regenerate demand fields when seasons change
        self.num_seasons_spin.valueChanged.connect(self._rebuild_seasons_and_demand)
        self._rebuild_seasons_and_demand()

        # solve button at bottom of left panel
        self.solve_button = QPushButton("Solve Optimization")
        self.solve_button.clicked.connect(self.solve_optimization)
        self.solve_button.setSizePolicy(QSizePolicy.Policy.Expanding,
                                        QSizePolicy.Policy.Fixed)
        scroll_layout.addWidget(self.solve_button)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        left_layout_outer.addWidget(scroll)

    # Build season structure + demand spinboxes in one place
    def _rebuild_seasons_and_demand(self):
        # clear existing demand layout
        self.clear_layout(self.demand_layout)

        num_seasons = self.num_seasons_spin.value()
        base = 12 // num_seasons
        rem = 12 % num_seasons
        idx = 0

        self.seasons_months = []
        self.season_demand_spinboxes = []

        for i in range(num_seasons):
            length = base + (1 if i < rem else 0)
            end_idx = idx + length - 1
            season_months = self.months_full[idx:end_idx + 1]
            self.seasons_months.append(season_months)

            row = QHBoxLayout()
            row.setSpacing(6)

            lbl = QLabel(f"Season {i+1} ({season_months[0]}–{season_months[-1]}):")
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            sb = QSpinBox()
            sb.setRange(0, 10_000_000)
            sb.setValue(50000 if i == 2 else 30000)
            sb.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            sb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            row.addWidget(lbl)
            row.addWidget(sb)

            self.demand_layout.addLayout(row)
            self.season_demand_spinboxes.append(sb)

            idx += length

    # ---------- Right: steps / results as stacked ---------- #
    def _build_right_panel(self):
        right_layout = QVBoxLayout(self.right_container)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(6)

        self.right_stack = QStackedWidget()
        self.right_stack.setSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Expanding)

        # simple "description" page instead of wizard steps
        intro_page = QWidget()
        intro_layout = QVBoxLayout(intro_page)
        intro_title = QLabel("Production Planning")
        intro_title.setFont(self.font_title)
        intro_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro_text = QLabel(
            "Fill parameters and seasonal demand on the left.\n"
            "Then click 'Solve Optimization' to compute the optimal plan."
        )
        intro_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro_text.setWordWrap(True)

        intro_layout.addStretch()
        intro_layout.addWidget(intro_title)
        intro_layout.addWidget(intro_text)
        intro_layout.addStretch()

        self.right_stack.addWidget(intro_page)  # index 0

        right_layout.addWidget(self.right_stack)

    # ---------- Create results view (tabs) ---------- #
    def create_results_view(self):
        if self.results_widget:
            # just switch
            self.right_stack.setCurrentWidget(self.results_widget)
            return

        self.results_widget = QWidget()
        layout = QVBoxLayout(self.results_widget)

        tabs = QTabWidget()
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        self.table_tab = QWidget()
        self.graph_tab = QWidget()
        self.detail_tab = QWidget()

        tabs.addTab(self.table_tab, "Detailed Table")
        tabs.addTab(self.graph_tab, "Graphs")
        tabs.addTab(self.detail_tab, "Monthly View")

        # table tab
        table_layout = QVBoxLayout(self.table_tab)
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(9)
        self.result_table.setHorizontalHeaderLabels([
            'Month', 'Demand', 'Production', 'Workers', 'Hired', 'Fired',
            'Overtime (hrs)', 'Stock', 'Monthly Cost'
        ])
        self.result_table.setSizePolicy(QSizePolicy.Policy.Expanding,
                                        QSizePolicy.Policy.Expanding)
        table_layout.addWidget(self.result_table)

        # graphs tab
        graph_layout = QVBoxLayout(self.graph_tab)
        self.figure = Figure(facecolor='#121212')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding,
                                  QSizePolicy.Policy.Expanding)
        graph_layout.addWidget(self.canvas)

        # detail tab
        detail_layout = QVBoxLayout(self.detail_tab)
        self.detail_grid = QGridLayout()
        detail_layout.addLayout(self.detail_grid)
        detail_layout.addStretch()

        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("Previous Month")
        self.btn_next = QPushButton("Next Month")
        self.btn_prev.clicked.connect(self.prev_month)
        self.btn_next.clicked.connect(self.next_month)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        detail_layout.addLayout(nav_layout)

        layout.addWidget(tabs)

        back_btn = QPushButton("Back to Inputs")
        back_btn.clicked.connect(self.back_to_inputs)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.right_stack.addWidget(self.results_widget)
        self.right_stack.setCurrentWidget(self.results_widget)

    # ---------- Monthly detail & graphs ---------- #
    def update_monthly_detail(self):
        if not hasattr(self, 'monthly_data'):
            return

        data = self.monthly_data[self.current_month_idx]
        month = data['month']
        prev_workers = self.monthly_data[self.current_month_idx - 1]['workers'] if self.current_month_idx > 0 else float(self.inputs["Initial Workers"].text())

        for i in reversed(range(self.detail_grid.count())):
            w = self.detail_grid.itemAt(i).widget()
            if w:
                w.deleteLater()

        title = QLabel(f"{month} — Monthly Overview")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00bcd4;")
        self.detail_grid.addWidget(title, 0, 0, 1, 4)

        diff = data['workers'] - prev_workers
        diff_text = f"+{int(diff)}" if diff >= 0 else f"{int(diff)}"
        color = "#4caf50" if diff >= 0 else "#f44336"

        workers_lbl = QLabel(f"Workers: {int(data['workers'])}")
        workers_lbl.setFont(QFont("Segoe UI", 13))
        self.detail_grid.addWidget(workers_lbl, 1, 0, 1, 2)

        change_lbl = QLabel(diff_text)
        change_lbl.setStyleSheet(f"color: {color}; font-size: 22pt; font-weight: bold;")
        self.detail_grid.addWidget(change_lbl, 1, 2, 1, 2)

        hired = int(data['hired'])
        fired = int(data['fired'])
        if hired > 0:
            self.detail_grid.addWidget(QLabel(f"Hired: {hired}"), 2, 0, 1, 2)
        if fired > 0:
            self.detail_grid.addWidget(QLabel(f"Fired: {fired}"), 2, 2, 1, 2)

        ot_hours = data['overtime']
        ot_cost = ot_hours * float(self.inputs["Overtime Hourly Rate"].text())
        self.detail_grid.addWidget(QLabel("Overtime"), 3, 0)
        self.detail_grid.addWidget(QLabel(f"{ot_hours:.1f} hours"), 3, 1)
        self.detail_grid.addWidget(QLabel(f"Cost: ${ot_cost:,.0f}"), 3, 2)

        self.detail_grid.addWidget(QLabel("Stock Level"), 4, 0)
        stock_value = QLabel(f"{int(data['stock'])} units")
        stock_value.setFont(QFont("Segoe UI", 16))
        self.detail_grid.addWidget(stock_value, 4, 1, 1, 3)

        self.detail_grid.addWidget(QLabel(f"Production: {data['production']:.0f} units"), 5, 0, 1, 2)
        self.detail_grid.addWidget(QLabel(f"Demand: {data['demand']:.0f} units"), 5, 2, 1, 2)

        self.btn_prev.setEnabled(self.current_month_idx > 0)
        self.btn_next.setEnabled(self.current_month_idx < 11)

    def prev_month(self):
        if self.current_month_idx > 0:
            self.current_month_idx -= 1
            self.update_monthly_detail()

    def next_month(self):
        if self.current_month_idx < 11:
            self.current_month_idx += 1
            self.update_monthly_detail()

    def update_graphs(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1e1e1e')
        self.figure.patch.set_facecolor('#121212')
        ax.tick_params(colors='white')
        for side in ('bottom', 'top', 'left', 'right'):
            ax.spines[side].set_color('white')

        months = [d['month'] for d in self.monthly_data]
        production = [d['production'] for d in self.monthly_data]
        demand = [d['demand'] for d in self.monthly_data]
        stock = [d['stock'] for d in self.monthly_data]
        workers = [d['workers'] for d in self.monthly_data]

        ax.plot(months, production, label='Production', marker='o', color='#00bcd4')
        ax.plot(months, demand, label='Demand', marker='s', color='#ff9800')
        ax.plot(months, stock, label='Stock', marker='^', color='#4caf50')
        ax.bar(months, workers, alpha=0.4, label='Workers', color='#e91e63')

        ax.set_title("Production Planning Overview", color='white', fontsize=14)
        ax.set_xlabel("Month", color='white')
        ax.set_ylabel("Units / Workers", color='white')
        ax.legend(facecolor='#1e1e1e', labelcolor='white')
        ax.grid(True, color='#333333')

        self.canvas.draw()

    # ---------- Optimization & navigation ---------- #
    def solve_optimization(self):
        try:
            # parse parameters
            params = {k.replace(" ", "_").lower(): float(v.text()) for k, v in self.inputs.items()}
            num_seasons = self.num_seasons_spin.value()

            demand = []
            flat_months = []
            for sb, season in zip(self.season_demand_spinboxes, self.seasons_months):
                season_total = sb.value()
                monthly = season_total / len(season)
                demand.extend([monthly] * len(season))
                flat_months.extend(season)

            if len(flat_months) != 12:
                QMessageBox.warning(self, "Error", "Seasons must cover all 12 months.")
                return

            model = grb.Model("ProductionPlanning")
            periods = 12
            production = model.addVars(periods, lb=0, name="Prod")
            workers = model.addVars(periods, vtype=grb.GRB.INTEGER, name="Workers")
            overtime = model.addVars(periods, lb=0, name="OT")
            stock = model.addVars(periods, lb=0, name="Stock")
            hired = model.addVars(periods, vtype=grb.GRB.INTEGER, name="Hired")
            fired = model.addVars(periods, vtype=grb.GRB.INTEGER, name="Fired")

            obj = grb.quicksum(
                params["worker_salary"] * workers[t] +
                params["overtime_hourly_rate"] * overtime[t] +
                params["material_cost_per_unit"] * production[t] +
                params["storage_cost_per_unit"] * stock[t] +
                params["recruitment_cost"] * hired[t] +
                params["layoff_cost"] * fired[t]
                for t in range(periods)
            )
            model.setObjective(obj, grb.GRB.MINIMIZE)

            for t in range(periods):
                if t == 0:
                    model.addConstr(stock[0] == params["initial_stock"] + production[0] - demand[0])
                else:
                    model.addConstr(stock[t] == stock[t-1] + production[t] - demand[t])
                model.addConstr(
                    workers[t] * params["regular_hours_per_worker"] + overtime[t]
                    == production[t] * params["work_hours_per_unit"]
                )
                model.addConstr(overtime[t] <= params["max_overtime_hours"] * workers[t])
                model.addConstr(stock[t] >= 0)
                prev = workers[t-1] if t > 0 else params["initial_workers"]
                model.addConstr(workers[t] == prev + hired[t] - fired[t])

            model.addConstr(stock[11] >= params["desired_final_stock"])
            model.optimize()

            if model.Status != grb.GRB.OPTIMAL:
                QMessageBox.information(self, "No Solution", "No optimal solution found.")
                return

            self.monthly_data = []
            total_cost = 0
            for t in range(12):
                p = production[t].X
                w = workers[t].X
                o = overtime[t].X
                s = stock[t].X
                h = hired[t].X
                f = fired[t].X
                cost = (
                    params["worker_salary"] * w +
                    params["overtime_hourly_rate"] * o +
                    params["material_cost_per_unit"] * p +
                    params["storage_cost_per_unit"] * s +
                    params["recruitment_cost"] * h +
                    params["layoff_cost"] * f
                )
                total_cost += cost
                self.monthly_data.append({
                    'month': flat_months[t],
                    'demand': demand[t],
                    'production': p,
                    'workers': w,
                    'hired': h,
                    'fired': f,
                    'overtime': o,
                    'stock': s,
                    'cost': cost
                })

            self.create_results_view()

            # fill table
            self.result_table.setRowCount(12)
            for i, d in enumerate(self.monthly_data):
                self.result_table.setItem(i, 0, QTableWidgetItem(d['month']))
                self.result_table.setItem(i, 1, QTableWidgetItem(f"{d['demand']:.0f}"))
                self.result_table.setItem(i, 2, QTableWidgetItem(f"{d['production']:.0f}"))
                self.result_table.setItem(i, 3, QTableWidgetItem(f"{int(d['workers'])}"))
                self.result_table.setItem(i, 4, QTableWidgetItem(f"{int(d['hired'])}"))
                self.result_table.setItem(i, 5, QTableWidgetItem(f"{int(d['fired'])}"))
                self.result_table.setItem(i, 6, QTableWidgetItem(f"{d['overtime']:.1f}"))
                self.result_table.setItem(i, 7, QTableWidgetItem(f"{int(d['stock'])}"))
                self.result_table.setItem(i, 8, QTableWidgetItem(f"${d['cost']:,.0f}"))

            self.update_graphs()
            self.current_month_idx = 0
            self.update_monthly_detail()

            QMessageBox.information(
                self,
                "Success",
                f"Optimal solution found!\nTotal Annual Cost: ${total_cost:,.0f}"
            )

        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error", f"{e}\n\n{tb}")
            print(tb, file=sys.stderr)

    def back_to_inputs(self):
        self.right_stack.setCurrentIndex(0)

    # ---------- utility ---------- #
    def clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = OptimizationApp()
    win.show()
    sys.exit(app.exec())
