# config_example.py
"""
Configuration example for customizing the inspection routing system.
Copy this to config.py and modify for your specific needs.
"""

# ============================================================================
# SOLVER CONFIGURATION
# ============================================================================

# Default time limit for Gurobi (seconds)
SOLVER_TIME_LIMIT = 60

# Travel speed for distance calculations (km/h)
DEFAULT_SPEED_KMH = 40.0

# Big-M coefficient for constraint formulation
BIG_M = 1e4

# ============================================================================
# INSPECTOR CONFIGURATION
# ============================================================================

# Available skills in the system
AVAILABLE_SKILLS = [
    "electrical",
    "safety",
    "quality",
    "structural",
    "environmental"
]

# Default inspector settings
DEFAULT_INSPECTOR = {
    "max_work_hours": 8.0,
    "availability_start": 6,      # 6:00 AM
    "availability_end": 18,       # 6:00 PM
}

# ============================================================================
# TASK CONFIGURATION
# ============================================================================

# Difficulty levels
DIFFICULTY_LEVELS = {
    1: {"name": "Easy", "multiplier": 0.5},
    2: {"name": "Medium", "multiplier": 0.75},
    3: {"name": "Normal", "multiplier": 1.0},
    4: {"name": "Hard", "multiplier": 1.5},
    5: {"name": "Very Hard", "multiplier": 2.0},
}

# Priority levels
PRIORITY_LEVELS = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Critical",
    5: "Urgent",
}

# Default task time window
DEFAULT_TASK_TW_START = 8      # 8:00 AM
DEFAULT_TASK_TW_END = 17       # 5:00 PM

# ============================================================================
# DATASET GENERATION
# ============================================================================

# Grid size for random coordinate generation (0 to GRID_SIZE)
GRID_SIZE = 100

# Default dataset sizes
DEFAULT_NUM_INSPECTORS = 3
DEFAULT_NUM_TASKS = 10

# ============================================================================
# UI CONFIGURATION
# ============================================================================

# Main window dimensions
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# Color scheme for routes visualization
ROUTE_COLORS = [
    "#00AA00",  # green
    "#8B00FF",  # purple
    "#FF8800",  # orange
    "#00FFFF",  # cyan
    "#FF00FF",  # magenta
    "#8B4513",  # brown
    "#FFB6C1",  # pink
]

# Map marker sizes
DEPOT_MARKER_SIZE = 200
TASK_MARKER_SIZE = 80

# ============================================================================
# FILE PATHS
# ============================================================================

# Default export directory
EXPORT_DIR = "./exports"

# Sample data files
SAMPLE_INSPECTORS_CSV = "data/inspectors.csv"
SAMPLE_TASKS_CSV = "data/tasks.csv"

# ============================================================================
# CONSTRAINTS & RULES
# ============================================================================

# Enable/disable specific constraints
CONSTRAINTS = {
    "skill_matching": True,           # Require skill match
    "time_windows": True,             # Enforce time windows
    "work_hours": True,               # Enforce max work hours
    "inspector_availability": True,   # Enforce availability windows
}

# Penalty weights for soft constraints (if implemented)
PENALTIES = {
    "unassigned_task": 1000.0,
    "time_window_violation": 500.0,
    "work_hour_violation": 500.0,
}

# ============================================================================
# OPTIMIZATION STRATEGIES
# ============================================================================

# Gurobi parameter overrides
GUROBI_PARAMS = {
    "TimeLimit": SOLVER_TIME_LIMIT,
    "MIPGap": 0.01,              # 1% optimality gap
    "OutputFlag": 0,              # Silent mode
    "Threads": -1,                # Use all available threads
}

# ============================================================================
# REPORTING
# ============================================================================

# Fields to include in exported reports
REPORT_FIELDS = {
    "inspector_routes": True,
    "task_assignments": True,
    "travel_matrix": False,       # Large, not needed for small instances
    "detailed_timings": True,
}

# ============================================================================
# VALIDATION RULES
# ============================================================================

# Minimum/maximum values for inputs
VALIDATION = {
    "min_inspectors": 1,
    "max_inspectors": 50,
    "min_tasks": 1,
    "max_tasks": 200,
    "min_duration": 0.25,         # 15 minutes
    "max_duration": 8.0,          # Full work day
    "min_time_limit": 10,         # seconds
    "max_time_limit": 300,        # seconds
}

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Access configuration in your code:
    # from config import SOLVER_TIME_LIMIT, DEFAULT_SPEED_KMH, AVAILABLE_SKILLS
    
    print("Configuration Example Loaded")
    print(f"Default time limit: {SOLVER_TIME_LIMIT} seconds")
    print(f"Available skills: {', '.join(AVAILABLE_SKILLS)}")
    print(f"Route colors: {len(ROUTE_COLORS)} colors available")
