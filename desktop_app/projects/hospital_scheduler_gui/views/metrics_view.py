import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from hospital_scheduler.app.database import SessionLocal
from hospital_scheduler.app.models import Assignment, Employee

class MetricsView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)
        
        # Create Figure
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        self.ax1 = self.figure.add_subplot(121) # Workload
        self.ax2 = self.figure.add_subplot(122) # Cost

    def update_metrics(self, run_id):
        self.ax1.clear()
        self.ax2.clear()
        
        if not run_id:
            self.canvas.draw()
            return

        db = SessionLocal()
        try:
            assignments = db.query(Assignment).filter(Assignment.run_id == run_id).all()
            employees = db.query(Employee).all()
            emp_map = {e.employee_id: e for e in employees}
            
            # 1. Workload Data
            workload = {} # emp_name -> hours
            for a in assignments:
                name = emp_map[a.employee_id].name
                workload[name] = workload.get(name, 0) + a.hours
            
            # Sort by hours
            sorted_workload = sorted(workload.items(), key=lambda x: x[1], reverse=True)
            names = [x[0] for x in sorted_workload]
            hours = [x[1] for x in sorted_workload]
            
            # Bar Chart
            self.ax1.bar(names, hours, color='#3b82f6')
            self.ax1.set_title('Workload Distribution (Hours)')
            self.ax1.tick_params(axis='x', rotation=45, labelsize=8)
            
            # 2. Cost Data (By Role)
            cost_by_role = {}
            for a in assignments:
                role = emp_map[a.employee_id].role
                cost_by_role[role] = cost_by_role.get(role, 0) + a.cost
            
            # Donut Chart
            roles = list(cost_by_role.keys())
            costs = list(cost_by_role.values())
            
            wedges, texts, autotexts = self.ax2.pie(costs, labels=roles, autopct='%1.1f%%', 
                                                    startangle=90, colors=['#10b981', '#f59e0b', '#ef4444'])
            self.ax2.set_title('Cost Distribution by Role')
            
            # Draw circle for donut
            centre_circle = matplotlib.patches.Circle((0,0),0.70,fc='white')
            self.ax2.add_artist(centre_circle)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        finally:
            db.close()
