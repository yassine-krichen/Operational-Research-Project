"""
Utilitaires de visualisation pour les résultats
"""
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class VisualizationWidget(FigureCanvas):
    """Widget de visualisation basé sur Matplotlib"""
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def plot_gantt_chart(self, solution):
        """Affiche un diagramme de Gantt des affectations"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        if not solution or 'assignments' not in solution:
            ax.text(0.5, 0.5, 'Aucune solution à afficher', 
                   ha='center', va='center', transform=ax.transAxes)
            self.draw()
            return
        
        # Préparer les données
        stations = []
        colors = plt.cm.Set3(np.linspace(0, 1, 12))
        color_idx = 0
        
        for assignment in solution['assignments']:
            station_id = assignment['station']
            current_time = 0
            
            for task in assignment['tasks']:
                task_id = task['task_id']
                duration = task['duration']
                
                # Dessiner la barre
                ax.barh(station_id, duration, left=current_time, 
                       height=0.6, color=colors[color_idx % len(colors)],
                       edgecolor='black', linewidth=1)
                
                # Ajouter le label
                ax.text(current_time + duration/2, station_id, 
                       task_id, ha='center', va='center',
                       fontsize=8, fontweight='bold')
                
                current_time += duration
                color_idx += 1
        
        # Configuration
        ax.set_xlabel('Temps (minutes)', fontsize=10, fontweight='bold')
        ax.set_ylabel('Poste de travail', fontsize=10, fontweight='bold')
        ax.set_title('Diagramme de Gantt - Affectation des tâches', 
                    fontsize=12, fontweight='bold', pad=20)
        
        # Ligne de temps de cycle
        if 'cycle_time' in solution:
            ax.axvline(x=solution['cycle_time'], color='red', 
                      linestyle='--', linewidth=2, label=f"Temps de cycle: {solution['cycle_time']:.1f} min")
            ax.legend()
        
        ax.set_yticks([a['station'] for a in solution['assignments']])
        ax.set_yticklabels([f"Poste {a['station']}" for a in solution['assignments']])
        ax.grid(True, axis='x', alpha=0.3)
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_efficiency_bars(self, solution):
        """Affiche un graphique en barres de l'efficacité des postes"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        if not solution or 'assignments' not in solution:
            ax.text(0.5, 0.5, 'Aucune solution à afficher', 
                   ha='center', va='center', transform=ax.transAxes)
            self.draw()
            return
        
        stations = [f"Poste {a['station']}" for a in solution['assignments']]
        efficiencies = [a['efficiency'] for a in solution['assignments']]
        
        # Créer le graphique
        bars = ax.bar(stations, efficiencies, color='steelblue', edgecolor='black')
        
        # Colorier selon l'efficacité
        for i, bar in enumerate(bars):
            if efficiencies[i] >= 90:
                bar.set_color('green')
            elif efficiencies[i] >= 75:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        
        # Ajouter les valeurs sur les barres
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{efficiencies[i]:.1f}%',
                   ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylabel('Efficacité (%)', fontsize=10, fontweight='bold')
        ax.set_title('Efficacité par poste de travail', fontsize=12, fontweight='bold', pad=20)
        ax.set_ylim(0, 105)
        ax.axhline(y=100, color='black', linestyle='-', linewidth=0.5)
        ax.grid(True, axis='y', alpha=0.3)
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_workload_distribution(self, solution):
        """Affiche la distribution de la charge de travail"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        if not solution or 'assignments' not in solution:
            ax.text(0.5, 0.5, 'Aucune solution à afficher', 
                   ha='center', va='center', transform=ax.transAxes)
            self.draw()
            return
        
        stations = [f"P{a['station']}" for a in solution['assignments']]
        work_times = [a['total_time'] for a in solution['assignments']]
        idle_times = [a['idle_time'] for a in solution['assignments']]
        
        x = np.arange(len(stations))
        width = 0.6
        
        # Barres empilées
        p1 = ax.bar(x, work_times, width, label='Temps de travail', color='steelblue')
        p2 = ax.bar(x, idle_times, width, bottom=work_times, label='Temps inactif', color='lightgray')
        
        ax.set_ylabel('Temps (minutes)', fontsize=10, fontweight='bold')
        ax.set_title('Distribution de la charge de travail', fontsize=12, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(stations)
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
        
        # Ligne de temps de cycle
        if 'cycle_time' in solution:
            ax.axhline(y=solution['cycle_time'], color='red', 
                      linestyle='--', linewidth=2, label=f"Temps de cycle")
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_precedence_graph(self, model):
        """Affiche le graphe de précédence des tâches"""
        try:
            import networkx as nx
        except ImportError:
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, 'NetworkX requis pour afficher le graphe\npip install networkx', 
                   ha='center', va='center', transform=ax.transAxes)
            self.draw()
            return
        
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        # Créer le graphe
        G = nx.DiGraph()
        
        # Ajouter les nœuds
        for task in model.tasks:
            G.add_node(task)
        
        # Ajouter les arcs de précédence
        for (before, after) in model.precedences:
            G.add_edge(before, after)
        
        # Layout
        try:
            pos = nx.spring_layout(G, k=2, iterations=50)
        except:
            pos = nx.circular_layout(G)
        
        # Dessiner
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                              node_size=800, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=10, 
                               font_weight='bold', ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='gray', 
                              arrows=True, arrowsize=20, 
                              width=2, ax=ax)
        
        ax.set_title('Graphe de précédence des tâches', 
                    fontsize=12, fontweight='bold', pad=20)
        ax.axis('off')
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_summary_statistics(self, solution):
        """Affiche un résumé statistique"""
        self.fig.clear()
        
        if not solution:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, 'Aucune solution à afficher', 
                   ha='center', va='center', transform=ax.transAxes)
            self.draw()
            return
        
        # Créer 4 sous-graphiques
        gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 1. Indicateurs clés
        ax1 = self.fig.add_subplot(gs[0, 0])
        ax1.axis('off')
        
        summary_text = f"""
RÉSUMÉ DE LA SOLUTION

Nombre de postes: {int(solution.get('num_stations_used', 0))}
Temps de cycle: {solution.get('cycle_time', 0):.1f} min
Efficacité globale: {solution.get('summary', {}).get('overall_efficiency', 0):.1f}%
Perte d'équilibrage: {solution.get('summary', {}).get('balance_delay', 0):.1f}%

Statut: {solution.get('status', 'inconnu').upper()}
Temps de résolution: {solution.get('solve_time', 0):.2f} s
        """
        ax1.text(0.1, 0.5, summary_text, fontsize=10, 
                verticalalignment='center', fontfamily='monospace')
        
        # 2. Camembert efficacité
        if 'summary' in solution:
            ax2 = self.fig.add_subplot(gs[0, 1])
            efficiency = solution['summary'].get('overall_efficiency', 0)
            waste = 100 - efficiency
            
            ax2.pie([efficiency, waste], labels=['Utilisé', 'Inactif'],
                   autopct='%1.1f%%', colors=['green', 'lightgray'],
                   startangle=90)
            ax2.set_title('Utilisation globale', fontweight='bold')
        
        # 3. Nombre de tâches par poste
        if 'assignments' in solution:
            ax3 = self.fig.add_subplot(gs[1, 0])
            stations = [f"P{a['station']}" for a in solution['assignments']]
            task_counts = [len(a['tasks']) for a in solution['assignments']]
            
            ax3.bar(stations, task_counts, color='coral')
            ax3.set_ylabel('Nombre de tâches')
            ax3.set_title('Tâches par poste', fontweight='bold')
            ax3.grid(True, axis='y', alpha=0.3)
        
        # 4. Distribution des temps
        if 'assignments' in solution:
            ax4 = self.fig.add_subplot(gs[1, 1])
            times = [a['total_time'] for a in solution['assignments']]
            
            ax4.hist(times, bins=10, color='skyblue', edgecolor='black')
            ax4.axvline(x=solution.get('cycle_time', 0), color='red', 
                       linestyle='--', linewidth=2, label='Temps de cycle')
            ax4.set_xlabel('Temps (min)')
            ax4.set_ylabel('Fréquence')
            ax4.set_title('Distribution des temps', fontweight='bold')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        
        self.draw()
