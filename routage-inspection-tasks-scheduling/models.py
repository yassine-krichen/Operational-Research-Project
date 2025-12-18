# models.py
"""
Utility data models for the inspection routing system.
Defines structured data classes for Inspectors, Tasks, and Results.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Inspector:
    """Represents an inspector with skills, availability, and work constraints."""
    id: str
    name: str
    skills: List[str]
    max_work_hours: float
    location: tuple  # (x, y) starting location
    availability_start: int  # hour (0-23)
    availability_end: int    # hour (0-23)
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Task:
    """Represents an inspection task with location, time window, and skill requirement."""
    id: int
    name: str
    x: float
    y: float
    duration: float  # hours
    required_skill: str  # required skill
    difficulty: int  # 1 (easy) to 5 (hard) - affects inspector capability
    tw_start: int  # earliest start time (hour)
    tw_end: int    # latest completion time (hour)
    priority: int = 1  # 1 (normal) to 5 (urgent)
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Depot:
    """Represents the starting depot location."""
    id: int = 0
    name: str = "Depot"
    x: float = 0.0
    y: float = 0.0
    duration: float = 0.0
    tw_start: int = 0
    tw_end: int = 24
    required_skill: Optional[str] = None


@dataclass
class RouteSolution:
    """Represents the solution for one inspector's route."""
    inspector_id: str
    route: List[int]  # sequence of task IDs (0 = depot)
    travel_time: float
    service_time: float
    total_time: float
    tasks_completed: int


@dataclass
class SolutionResult:
    """Overall solution result containing all routes and metrics."""
    objective_value: float
    total_travel_time: float
    total_service_time: float
    routes: Dict[str, RouteSolution]
    solver_status: str
    solve_time: float
    gap: Optional[float] = None  # MIP gap if not optimal
    
    def summary(self) -> str:
        """Return a formatted summary of the solution."""
        lines = [
            f"Total Travel Distance: {self.total_travel_time:.2f} hours",
            f"Total Service Time: {self.total_service_time:.2f} hours",
            f"Objective Value: {self.objective_value:.3f}",
            f"Solver Status: {self.solver_status}",
            f"Solve Time: {self.solve_time:.2f} seconds",
        ]
        if self.gap is not None:
            lines.append(f"MIP Gap: {self.gap:.2%}")
        return "\n".join(lines)
