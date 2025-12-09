from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel)
from PyQt6.QtCore import Qt
from hospital_scheduler.app.database import SessionLocal
from hospital_scheduler.app.models import Demand, Shift

class DemandsView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        self.label = QLabel("Shift Demands (Requirements)")
        self.label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(self.label)
        
        self.table = QTableWidget()
        self.layout.addWidget(self.table)
        
        self.refresh_data()

    def refresh_data(self):
        db = SessionLocal()
        try:
            demands = db.query(Demand).order_by(Demand.date, Demand.shift_id).all()
            shifts = db.query(Shift).all()
            shift_map = {s.shift_id: s.name for s in shifts}
            
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["Date", "Shift", "Skill", "Required Count"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            self.table.setRowCount(len(demands))
            
            for i, d in enumerate(demands):
                # Date
                self.table.setItem(i, 0, QTableWidgetItem(d.date.strftime("%Y-%m-%d")))
                
                # Shift Name
                shift_name = shift_map.get(d.shift_id, d.shift_id)
                self.table.setItem(i, 1, QTableWidgetItem(shift_name))
                
                # Skill
                self.table.setItem(i, 2, QTableWidgetItem(d.skill))
                
                # Required
                item_req = QTableWidgetItem(str(d.required))
                item_req.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 3, item_req)
                
        finally:
            db.close()
