"""
Modèle mathématique PLNE pour l'équilibrage de chaîne de traitement de dossiers
"""

class LineBalancingModel:
    """
    Modèle d'optimisation pour l'affectation des tâches aux postes de travail
    
    Variables de décision:
    - x[i,j] : binaire, 1 si la tâche i est affectée au poste j, 0 sinon
    - y[j] : binaire, 1 si le poste j est utilisé, 0 sinon
    - CT : temps de cycle (temps max par poste)
    - T[j] : temps total du poste j
    
    Fonction objectif (deux modes):
    Mode 1: Minimiser le nombre de postes (avec temps de cycle fixé)
    Mode 2: Minimiser le temps de cycle (avec nombre de postes fixé)
    
    Contraintes:
    1. Chaque tâche affectée exactement à un poste
    2. Contraintes de précédence
    3. Temps total d'un poste ≤ temps de cycle
    4. Contraintes de compétences
    5. Équilibrage de charge
    6. Contraintes de compatibilité entre tâches
    """
    
    def __init__(self):
        self.tasks = []  # Liste des tâches
        self.num_tasks = 0
        self.num_stations = 0
        self.task_times = {}  # Temps d'exécution de chaque tâche
        self.precedences = []  # Relations de précédence (i, j) : i avant j
        self.skills_required = {}  # Compétences requises par tâche
        self.station_skills = {}  # Compétences disponibles par poste
        self.incompatibilities = []  # Tâches incompatibles sur même poste
        self.cycle_time = None  # Temps de cycle cible
        self.optimization_mode = "minimize_stations"  # ou "minimize_cycle_time"
        
        # Paramètres avancés
        self.task_complexity = {}  # Niveau de complexité (1-5)
        self.task_priority = {}  # Priorité de traitement
        self.setup_times = {}  # Temps de préparation entre tâches
        self.resource_requirements = {}  # Ressources nécessaires
        self.quality_requirements = {}  # Niveau de qualité requis
        
    def add_task(self, task_id, duration, complexity=1, priority=1, 
                 skills=None, resources=None, quality_level=1):
        """Ajoute une tâche au problème"""
        self.tasks.append(task_id)
        self.task_times[task_id] = duration
        self.task_complexity[task_id] = complexity
        self.task_priority[task_id] = priority
        self.skills_required[task_id] = skills if skills else []
        self.resource_requirements[task_id] = resources if resources else []
        self.quality_requirements[task_id] = quality_level
        self.num_tasks = len(self.tasks)
        
    def add_precedence(self, task_before, task_after):
        """Ajoute une contrainte de précédence"""
        self.precedences.append((task_before, task_after))
        
    def add_incompatibility(self, task1, task2):
        """Deux tâches ne peuvent pas être sur le même poste"""
        self.incompatibilities.append((task1, task2))
        
    def add_setup_time(self, task1, task2, time):
        """Temps de préparation lors du passage de task1 à task2"""
        self.setup_times[(task1, task2)] = time
        
    def set_station_skills(self, station_id, skills):
        """Définit les compétences disponibles pour un poste"""
        self.station_skills[station_id] = skills
        
    def calculate_min_stations_lower_bound(self):
        """Calcule la borne inférieure du nombre de postes nécessaires"""
        total_time = sum(self.task_times.values())
        if self.cycle_time and self.cycle_time > 0:
            return int(total_time / self.cycle_time) + 1
        return 1
        
    def calculate_theoretical_cycle_time(self):
        """Calcule le temps de cycle théorique minimum"""
        if self.num_tasks == 0:
            return 0
        return max(self.task_times.values())
        
    def validate_data(self):
        """Valide la cohérence des données"""
        errors = []
        
        # Vérifier que toutes les tâches ont un temps > 0
        for task in self.tasks:
            if self.task_times.get(task, 0) <= 0:
                errors.append(f"Tâche {task}: temps invalide")
                
        # Vérifier les précédences
        for (before, after) in self.precedences:
            if before not in self.tasks or after not in self.tasks:
                errors.append(f"Précédence invalide: {before} -> {after}")
                
        # Vérifier les cycles dans les précédences
        if self._has_precedence_cycle():
            errors.append("Cycle détecté dans les contraintes de précédence")
            
        return errors
        
    def _has_precedence_cycle(self):
        """Détecte les cycles dans le graphe de précédence"""
        from collections import defaultdict, deque
        
        # Construire le graphe
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for task in self.tasks:
            in_degree[task] = 0
            
        for (before, after) in self.precedences:
            graph[before].append(after)
            in_degree[after] += 1
            
        # Tri topologique (Kahn's algorithm)
        queue = deque([task for task in self.tasks if in_degree[task] == 0])
        sorted_count = 0
        
        while queue:
            task = queue.popleft()
            sorted_count += 1
            
            for neighbor in graph[task]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        return sorted_count != len(self.tasks)
        
    def get_model_statistics(self):
        """Retourne des statistiques sur le modèle"""
        return {
            'num_tasks': self.num_tasks,
            'num_precedences': len(self.precedences),
            'num_incompatibilities': len(self.incompatibilities),
            'total_processing_time': sum(self.task_times.values()),
            'avg_task_time': sum(self.task_times.values()) / max(1, self.num_tasks),
            'max_task_time': max(self.task_times.values()) if self.task_times else 0,
            'min_task_time': min(self.task_times.values()) if self.task_times else 0,
            'theoretical_min_stations': self.calculate_min_stations_lower_bound(),
            'theoretical_min_cycle_time': self.calculate_theoretical_cycle_time()
        }
