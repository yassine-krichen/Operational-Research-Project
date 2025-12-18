"""
Solveur Gurobi pour le problème d'équilibrage de chaîne
"""
import gurobipy as gp
from gurobipy import GRB
from ..models.line_balancing import LineBalancingModel

class GurobiSolver:
    """Résout le problème d'équilibrage avec Gurobi"""
    
    def __init__(self, model: LineBalancingModel):
        self.model = model
        self.gurobi_model = None
        self.solution = None
        self.x_vars = {}  # Variables d'affectation x[i,j]
        self.y_vars = {}  # Variables d'utilisation de poste y[j]
        self.t_vars = {}  # Temps total par poste T[j]
        self.ct_var = None  # Temps de cycle
        
    def build_model(self):
        """Construit le modèle Gurobi"""
        # Créer le modèle
        self.gurobi_model = gp.Model("LineBalancing")
        
        # Paramètres
        tasks = self.model.tasks
        num_tasks = self.model.num_tasks
        num_stations = self.model.num_stations if self.model.num_stations > 0 else num_tasks
        
        # === VARIABLES DE DÉCISION ===
        
        # x[i,j] : tâche i affectée au poste j
        self.x_vars = {}
        for i in range(num_tasks):
            for j in range(num_stations):
                self.x_vars[i, j] = self.gurobi_model.addVar(
                    vtype=GRB.BINARY,
                    name=f"x_{tasks[i]}_{j}"
                )
        
        # y[j] : poste j est utilisé
        self.y_vars = {}
        for j in range(num_stations):
            self.y_vars[j] = self.gurobi_model.addVar(
                vtype=GRB.BINARY,
                name=f"y_{j}"
            )
        
        # T[j] : temps total du poste j
        self.t_vars = {}
        for j in range(num_stations):
            self.t_vars[j] = self.gurobi_model.addVar(
                vtype=GRB.CONTINUOUS,
                lb=0,
                name=f"T_{j}"
            )
        
        # CT : temps de cycle
        self.ct_var = self.gurobi_model.addVar(
            vtype=GRB.CONTINUOUS,
            lb=0,
            name="CycleTime"
        )
        
        self.gurobi_model.update()
        
        # === FONCTION OBJECTIF ===
        
        if self.model.optimization_mode == "minimize_stations":
            # Minimiser le nombre de postes utilisés
            self.gurobi_model.setObjective(
                gp.quicksum(self.y_vars[j] for j in range(num_stations)),
                GRB.MINIMIZE
            )
        else:  # minimize_cycle_time
            # Minimiser le temps de cycle
            self.gurobi_model.setObjective(self.ct_var, GRB.MINIMIZE)
        
        # === CONTRAINTES ===
        
        # C1: Chaque tâche est affectée à exactement un poste
        for i in range(num_tasks):
            self.gurobi_model.addConstr(
                gp.quicksum(self.x_vars[i, j] for j in range(num_stations)) == 1,
                name=f"assign_task_{tasks[i]}"
            )
        
        # C2: Contraintes de précédence
        # Si tâche i avant tâche k, alors poste(i) <= poste(k)
        for (task_before, task_after) in self.model.precedences:
            i = tasks.index(task_before)
            k = tasks.index(task_after)
            
            self.gurobi_model.addConstr(
                gp.quicksum(j * self.x_vars[i, j] for j in range(num_stations)) <=
                gp.quicksum(j * self.x_vars[k, j] for j in range(num_stations)),
                name=f"precedence_{task_before}_{task_after}"
            )
        
        # C3: Calcul du temps total par poste
        for j in range(num_stations):
            # Temps de base des tâches
            base_time = gp.quicksum(
                self.model.task_times[tasks[i]] * self.x_vars[i, j]
                for i in range(num_tasks)
            )
            
            # Ajouter les temps de setup si applicable
            setup_time = 0
            if self.model.setup_times:
                # Simplification: ajouter temps de setup moyen
                for (t1, t2), time in self.model.setup_times.items():
                    if t1 in tasks and t2 in tasks:
                        i1 = tasks.index(t1)
                        i2 = tasks.index(t2)
                        # Si les deux tâches sont sur le même poste
                        setup_time += time * self.x_vars[i1, j] * self.x_vars[i2, j]
            
            self.gurobi_model.addConstr(
                self.t_vars[j] >= base_time,
                name=f"time_station_{j}"
            )
        
        # C4: Le temps de chaque poste ne dépasse pas le temps de cycle
        for j in range(num_stations):
            self.gurobi_model.addConstr(
                self.t_vars[j] <= self.ct_var,
                name=f"cycle_time_limit_{j}"
            )
        
        # C5: Si un poste a des tâches, il est utilisé
        for j in range(num_stations):
            self.gurobi_model.addConstr(
                gp.quicksum(self.x_vars[i, j] for i in range(num_tasks)) <= 
                num_tasks * self.y_vars[j],
                name=f"station_used_{j}"
            )
        
        # C6: Temps de cycle fixé ou minimum
        if self.model.cycle_time is not None and self.model.optimization_mode == "minimize_stations":
            self.gurobi_model.addConstr(
                self.ct_var == self.model.cycle_time,
                name="fixed_cycle_time"
            )
        else:
            # Assurer un temps de cycle minimum réaliste
            min_cycle = max(self.model.task_times.values()) if self.model.task_times else 0
            self.gurobi_model.addConstr(
                self.ct_var >= min_cycle,
                name="min_cycle_time"
            )
        
        # C7: Contraintes de compétences
        for i in range(num_tasks):
            task = tasks[i]
            required_skills = self.model.skills_required.get(task, [])
            
            if required_skills:
                for j in range(num_stations):
                    station_skills = self.model.station_skills.get(j, [])
                    # Si les compétences requises ne sont pas disponibles, interdire l'affectation
                    if not all(skill in station_skills for skill in required_skills):
                        self.gurobi_model.addConstr(
                            self.x_vars[i, j] == 0,
                            name=f"skill_constraint_{task}_{j}"
                        )
        
        # C8: Contraintes d'incompatibilité
        for (task1, task2) in self.model.incompatibilities:
            if task1 in tasks and task2 in tasks:
                i1 = tasks.index(task1)
                i2 = tasks.index(task2)
                
                for j in range(num_stations):
                    self.gurobi_model.addConstr(
                        self.x_vars[i1, j] + self.x_vars[i2, j] <= 1,
                        name=f"incompatibility_{task1}_{task2}_{j}"
                    )
        
        # C9: Équilibrage de charge (variance minimale)
        # Les temps des postes utilisés doivent être équilibrés
        # Note: Contrainte optionnelle pour meilleur équilibrage
        # Désactivée par défaut pour garantir la faisabilité
        # for j in range(num_stations):
        #     self.gurobi_model.addConstr(
        #         self.t_vars[j] <= self.ct_var,
        #         name=f"balance_{j}"
        #     )
        
        # C10: Symétrie breaking - ordonner les postes
        for j in range(num_stations - 1):
            self.gurobi_model.addConstr(
                self.y_vars[j] >= self.y_vars[j + 1],
                name=f"symmetry_{j}"
            )
    
    def solve(self, time_limit=300, mip_gap=0.01, log_output=True):
        """
        Résout le modèle
        
        Args:
            time_limit: Limite de temps en secondes
            mip_gap: Gap d'optimalité acceptable (1% par défaut)
            log_output: Afficher les logs Gurobi
        """
        if self.gurobi_model is None:
            self.build_model()
        
        # Paramètres de résolution
        self.gurobi_model.setParam('TimeLimit', time_limit)
        self.gurobi_model.setParam('MIPGap', mip_gap)
        self.gurobi_model.setParam('OutputFlag', 1 if log_output else 0)
        
        # Résoudre
        self.gurobi_model.optimize()
        
        # Extraire la solution
        status = self.gurobi_model.status
        if status == GRB.OPTIMAL:
            self.extract_solution()
            return True
        elif status == GRB.TIME_LIMIT and self.gurobi_model.SolCount > 0:
            # Solution sous-optimale trouvée
            self.extract_solution()
            return True
        elif status == GRB.INFEASIBLE:
            print("Modèle infaisable. Calcul de l'IIS...")
            self.gurobi_model.computeIIS()
            print("Contraintes en conflit :")
            for c in self.gurobi_model.getConstrs():
                if c.IISConstr:
                    print(f"  - {c.ConstrName}")
            return False
        
        return False
    
    def extract_solution(self):
        """Extrait la solution du modèle Gurobi"""
        status = self.gurobi_model.status
        if status not in [GRB.OPTIMAL, GRB.TIME_LIMIT]:
            return None
        
        # Vérifier qu'une solution existe
        if self.gurobi_model.SolCount == 0:
            return None
        
        tasks = self.model.tasks
        num_stations = self.model.num_stations if self.model.num_stations > 0 else len(tasks)
        
        status_text = 'optimal' if self.gurobi_model.status == GRB.OPTIMAL else 'feasible'
        
        self.solution = {
            'status': status_text,
            'objective_value': self.gurobi_model.objVal,
            'cycle_time': self.ct_var.X,
            'num_stations_used': int(sum(self.y_vars[j].X for j in range(num_stations))),
            'assignments': [],
            'station_stats': [],
            'mip_gap': self.gurobi_model.MIPGap,
            'solve_time': self.gurobi_model.Runtime
        }
        
        # Affectations
        for j in range(num_stations):
            if self.y_vars[j].X > 0.5:  # Poste utilisé
                station_tasks = []
                for i in range(len(tasks)):
                    if self.x_vars[i, j].X > 0.5:
                        station_tasks.append({
                            'task_id': tasks[i],
                            'duration': self.model.task_times[tasks[i]],
                            'complexity': self.model.task_complexity.get(tasks[i], 1),
                            'priority': self.model.task_priority.get(tasks[i], 1)
                        })
                
                if station_tasks:
                    total_time = sum(t['duration'] for t in station_tasks)
                    self.solution['assignments'].append({
                        'station': j + 1,
                        'tasks': station_tasks,
                        'total_time': total_time,
                        'idle_time': self.ct_var.X - total_time,
                        'efficiency': (total_time / self.ct_var.X * 100) if self.ct_var.X > 0 else 0
                    })
        
        # Statistiques
        total_time = sum(self.model.task_times.values())
        total_available = self.solution['cycle_time'] * self.solution['num_stations_used']
        
        self.solution['summary'] = {
            'total_processing_time': total_time,
            'total_available_time': total_available,
            'overall_efficiency': (total_time / total_available * 100) if total_available > 0 else 0,
            'balance_delay': ((total_available - total_time) / total_available * 100) if total_available > 0 else 0
        }
        
        return self.solution
    
    def get_model_info(self):
        """Retourne des informations sur le modèle"""
        if self.gurobi_model is None:
            return None
        
        return {
            'num_variables': self.gurobi_model.NumVars,
            'num_constraints': self.gurobi_model.NumConstrs,
            'num_binary_vars': self.gurobi_model.NumBinVars,
            'num_continuous_vars': self.gurobi_model.NumVars - self.gurobi_model.NumBinVars
        }
