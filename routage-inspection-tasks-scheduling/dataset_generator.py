# dataset_generator.py
"""
Dataset generator for the inspection routing system.
Supports both random and structured dataset generation for testing and real-world scenarios.
"""

import random
from typing import List, Tuple
from models import Inspector, Task, Depot


class DatasetGenerator:
    """Generates inspection scheduling datasets with various configurations."""
    
    SKILL_POOL = ["electrical", "safety", "quality", "structural", "environmental"]
    DIFFICULTY_MULTIPLIER = {1: 0.5, 2: 0.75, 3: 1.0, 4: 1.5, 5: 2.0}
    
    def __init__(self, seed: int = None):
        """Initialize with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
    
    @staticmethod
    def generate_inspectors(
        count: int = 3,
        skills_per_inspector: int = 2,
        max_work_hours: float = 8.0,
        grid_size: int = 100,
        structured: bool = False,
    ) -> List[Inspector]:
        """
        Generate a list of inspectors.
        
        Args:
            count: Number of inspectors
            skills_per_inspector: How many skills each inspector has
            max_work_hours: Maximum work hours per inspector
            grid_size: Coordinate space size
            structured: If True, use predefined; if False, randomize
        
        Returns:
            List of Inspector objects
        """
        if structured:
            return DatasetGenerator._generate_inspectors_structured(
                max_work_hours, grid_size
            )
        
        inspectors = []
        for i in range(count):
            skills = random.sample(
                DatasetGenerator.SKILL_POOL,
                min(skills_per_inspector, len(DatasetGenerator.SKILL_POOL))
            )
            x = random.uniform(0, grid_size)
            y = random.uniform(0, grid_size)
            availability_start = random.randint(6, 8)
            availability_end = random.randint(16, 18)
            
            inspector = Inspector(
                id=f"I{i+1}",
                name=f"Inspector {chr(65+i)}",
                skills=skills,
                max_work_hours=max_work_hours,
                location=(x, y),
                availability_start=availability_start,
                availability_end=availability_end,
            )
            inspectors.append(inspector)
        
        return inspectors
    
    @staticmethod
    def _generate_inspectors_structured(
        max_work_hours: float,
        grid_size: int,
    ) -> List[Inspector]:
        """Generate a predefined set of inspectors for consistent testing."""
        return [
           
            Inspector(
                id="I2",
                name="Inspector B",
                skills=["electrical", "structural"],
                max_work_hours=8.0,
                location=(36.3, 13.8),
                availability_start=7,
                availability_end=16,
            ),
          
            Inspector(
                id="I4",
                name="Inspector D",
                skills=["environmental", "quality", "safety"],
                max_work_hours=8.0,
                location=(18.8, 40.7),
                availability_start=8,
                availability_end=16,
            ),
            Inspector(
                id="I5",
                name="Inspector E",
                skills=["electrical", "safety"],
                max_work_hours=8.0,
                location=(52.2, 26.1),
                availability_start=8,
                availability_end=16,
            ),
            Inspector(
                id="I6",
                name="Inspector F",
                skills=["quality", "safety"],
                max_work_hours=8.0,
                location=(50.6, 20.9),
                availability_start=6,
                availability_end=17,
            ),
        ]
    
    @staticmethod
    def generate_tasks(
        count: int = 10,
        grid_size: int = 100,
        structured: bool = False,
    ) -> List[Task]:
        """
        Generate a list of inspection tasks.
        
        Args:
            count: Number of tasks
            grid_size: Coordinate space size
            structured: If True, use predefined; if False, randomize
        
        Returns:
            List of Task objects
        """
        if structured:
            return DatasetGenerator._generate_tasks_structured()
        
        tasks = []
        for i in range(1, count + 1):
            x = random.uniform(0, grid_size)
            y = random.uniform(0, grid_size)
            duration = random.uniform(0.5, 2.0)
            required_skill = random.choice(DatasetGenerator.SKILL_POOL)
            difficulty = random.randint(1, 5)
            tw_start = random.randint(8, 12)
            tw_end = tw_start + random.randint(4, 8)
            priority = random.randint(1, 3)
            
            task = Task(
                id=i,
                name=f"Task {i}",
                x=x,
                y=y,
                duration=duration,
                required_skill=required_skill,
                difficulty=difficulty,
                tw_start=tw_start,
                tw_end=tw_end,
                priority=priority,
            )
            tasks.append(task)
        
        return tasks
    
    @staticmethod
    def _generate_tasks_structured() -> List[Task]:
        """Generate a predefined set of tasks for consistent testing."""
        return [
            # Tasks positioned as shown in the screenshot
            Task(id=1, name="Task 1", x=20, y=33, duration=0.5, 
                 required_skill="electrical", difficulty=1, tw_start=8, tw_end=18, priority=1),
            Task(id=2, name="Task 2", x=25, y=25, duration=0.5, 
                 required_skill="quality", difficulty=1, tw_start=8, tw_end=18, priority=1),
            Task(id=3, name="Task 3", x=18, y=42, duration=0.5, 
                 required_skill="safety", difficulty=1, tw_start=8, tw_end=18, priority=1),
            Task(id=4, name="Task 4", x=35, y=28, duration=0.5, 
                 required_skill="electrical", difficulty=1, tw_start=8, tw_end=18, priority=1),
            Task(id=5, name="Task 5", x=50, y=20, duration=0.5, 
                 required_skill="quality", difficulty=1, tw_start=8, tw_end=18, priority=1),
            Task(id=6, name="Task 6", x=55, y=12, duration=0.5, 
                 required_skill="safety", difficulty=1, tw_start=8, tw_end=18, priority=1),
            Task(id=7, name="Task 7", x=38, y=48, duration=0.5, 
                 required_skill="quality", difficulty=1, tw_start=8, tw_end=18, priority=1),
            Task(id=8, name="Task 8", x=30, y=40, duration=0.5, 
                 required_skill="electrical", difficulty=1, tw_start=8, tw_end=18, priority=1),
            Task(id=9, name="Task 9", x=50, y=38, duration=0.5, 
                 required_skill="safety", difficulty=1, tw_start=8, tw_end=18, priority=1),
            Task(id=10, name="Task 10", x=40, y=30, duration=0.5, 
                 required_skill="quality", difficulty=1, tw_start=8, tw_end=18, priority=1),
        ]
    
    @staticmethod
    def generate_dataset(
        num_inspectors: int = 3,
        num_tasks: int = 10,
        structured: bool = True,
        seed: int = None,
    ) -> Tuple[List[Inspector], List[Task], Depot]:
        """
        Generate a complete dataset: inspectors, tasks, and depot.
        
        Args:
            num_inspectors: Number of inspectors
            num_tasks: Number of tasks
            structured: Use predefined structured data if True
            seed: Random seed for reproducibility
        
        Returns:
            Tuple of (inspectors, tasks, depot)
        """
        gen = DatasetGenerator(seed=seed)
        
        inspectors = gen.generate_inspectors(
            count=num_inspectors,
            structured=structured
        )
        tasks = gen.generate_tasks(
            count=num_tasks,
            structured=structured
        )
        depot = Depot()
        
        return inspectors, tasks, depot
