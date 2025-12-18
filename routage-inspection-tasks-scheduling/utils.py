# utils.py
"""
Utility functions for data import/export and reporting.
"""

import json
import csv
from typing import List, Dict, Any
from datetime import datetime
from models import Inspector, Task, Depot, SolutionResult


class DataExporter:
    """Export data and solutions to various formats."""
    
    @staticmethod
    def export_solution_json(solution: SolutionResult, filepath: str):
        """Export solution to JSON format."""
        data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "solver_status": solution.solver_status,
                "solve_time": solution.solve_time,
            },
            "summary": {
                "objective_value": solution.objective_value,
                "total_travel_time": solution.total_travel_time,
                "total_service_time": solution.total_service_time,
            },
            "routes": {
                ins_id: {
                    "route": route_sol.route,
                    "travel_time": route_sol.travel_time,
                    "service_time": route_sol.service_time,
                    "total_time": route_sol.total_time,
                    "tasks_completed": route_sol.tasks_completed,
                }
                for ins_id, route_sol in solution.routes.items()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def export_routes_csv(solution: SolutionResult, filepath: str):
        """Export routes to CSV format."""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Inspector ID", "Route", "Travel Time (h)", "Service Time (h)",
                "Total Time (h)", "Tasks Completed"
            ])
            
            for ins_id, route_sol in solution.routes.items():
                writer.writerow([
                    ins_id,
                    ";".join(map(str, route_sol.route)),
                    f"{route_sol.travel_time:.2f}",
                    f"{route_sol.service_time:.2f}",
                    f"{route_sol.total_time:.2f}",
                    route_sol.tasks_completed,
                ])
    
    @staticmethod
    def export_report_txt(
        solution: SolutionResult,
        inspectors: List[Inspector],
        tasks: List[Task],
        filepath: str
    ):
        """Export comprehensive report to text file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("INSPECTION ROUTING OPTIMIZATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            f.write("SOLUTION SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Objective Value (Total Travel Time): {solution.objective_value:.3f} hours\n")
            f.write(f"Total Travel Time: {solution.total_travel_time:.2f} hours\n")
            f.write(f"Total Service Time: {solution.total_service_time:.2f} hours\n")
            f.write(f"Solver Status: {solution.solver_status}\n")
            f.write(f"Solve Time: {solution.solve_time:.2f} seconds\n")
            if solution.gap is not None:
                f.write(f"MIP Gap: {solution.gap:.2%}\n")
            f.write("\n")
            
            # Inspectors
            f.write("INSPECTORS\n")
            f.write("-" * 80 + "\n")
            for insp in inspectors:
                f.write(f"\n{insp.id}: {insp.name}\n")
                f.write(f"  Skills: {', '.join(insp.skills)}\n")
                f.write(f"  Max Work Hours: {insp.max_work_hours}\n")
                f.write(f"  Location: ({insp.location[0]:.1f}, {insp.location[1]:.1f})\n")
                f.write(f"  Availability: {insp.availability_start}:00 - {insp.availability_end}:00\n")
            f.write("\n")
            
            # Tasks
            f.write("TASKS\n")
            f.write("-" * 80 + "\n")
            for task in tasks:
                f.write(f"\nTask {task.id}: {task.name}\n")
                f.write(f"  Location: ({task.x:.1f}, {task.y:.1f})\n")
                f.write(f"  Duration: {task.duration:.2f} hours\n")
                f.write(f"  Required Skill: {task.required_skill}\n")
                f.write(f"  Difficulty: {task.difficulty}/5\n")
                f.write(f"  Time Window: {task.tw_start}:00 - {task.tw_end}:00\n")
                f.write(f"  Priority: {'★' * task.priority}\n")
            f.write("\n")
            
            # Routes
            f.write("DETAILED ROUTES\n")
            f.write("=" * 80 + "\n")
            for ins_id, route_sol in solution.routes.items():
                f.write(f"\n{ins_id}\n")
                f.write(f"  Route: {' → '.join(map(str, route_sol.route))}\n")
                f.write(f"  Travel Time: {route_sol.travel_time:.2f} hours\n")
                f.write(f"  Service Time: {route_sol.service_time:.2f} hours\n")
                f.write(f"  Total Time: {route_sol.total_time:.2f} hours\n")
                f.write(f"  Tasks Completed: {route_sol.tasks_completed}\n")
                if route_sol.total_time > 0:
                    utilization = (route_sol.total_time / 8.0) * 100
                    f.write(f"  Inspector Utilization: {utilization:.1f}%\n")
            
            f.write("\n" + "=" * 80 + "\n")


class DataImporter:
    """Import data from various formats."""
    
    @staticmethod
    def import_tasks_csv(filepath: str) -> List[Task]:
        """Import tasks from CSV file."""
        tasks = []
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader, start=1):
                    task = Task(
                        id=int(row.get('id', idx)),
                        name=row.get('name', f'Task {idx}'),
                        x=float(row.get('x', 0)),
                        y=float(row.get('y', 0)),
                        duration=float(row.get('duration', 1.0)),
                        required_skill=row.get('skill', 'quality'),
                        difficulty=int(row.get('difficulty', 2)),
                        tw_start=int(row.get('tw_start', 8)),
                        tw_end=int(row.get('tw_end', 17)),
                    )
                    tasks.append(task)
        except Exception as e:
            raise ValueError(f"Error importing tasks from CSV: {e}")
        
        return tasks
    
    @staticmethod
    def import_inspectors_csv(filepath: str) -> List[Inspector]:
        """Import inspectors from CSV file."""
        inspectors = []
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    inspector = Inspector(
                        id=row.get('id', 'I1'),
                        name=row.get('name', 'Inspector'),
                        skills=row.get('skills', 'electrical,quality').split(','),
                        max_work_hours=float(row.get('max_hours', 8.0)),
                        location=(float(row.get('x', 0)), float(row.get('y', 0))),
                        availability_start=int(row.get('avail_start', 6)),
                        availability_end=int(row.get('avail_end', 18)),
                    )
                    inspectors.append(inspector)
        except Exception as e:
            raise ValueError(f"Error importing inspectors from CSV: {e}")
        
        return inspectors
