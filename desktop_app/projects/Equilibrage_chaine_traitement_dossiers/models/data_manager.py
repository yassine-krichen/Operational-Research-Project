"""
Gestionnaire de données pour le projet
"""
import json
import pandas as pd

class DataManager:
    """Gère le chargement et la sauvegarde des données"""
    
    @staticmethod
    def load_from_json(filepath):
        """Charge les données depuis un fichier JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    @staticmethod
    def save_to_json(data, filepath):
        """Sauvegarde les données dans un fichier JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    @staticmethod
    def export_solution_to_excel(solution, filepath):
        """Exporte la solution vers Excel"""
        # Créer les différentes feuilles
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Affectation des tâches
            if 'assignments' in solution:
                df_assign = pd.DataFrame(solution['assignments'])
                df_assign.to_excel(writer, sheet_name='Affectations', index=False)
                
            # Statistiques par poste
            if 'station_stats' in solution:
                df_stats = pd.DataFrame(solution['station_stats'])
                df_stats.to_excel(writer, sheet_name='Statistiques_Postes', index=False)
                
            # Résumé
            if 'summary' in solution:
                df_summary = pd.DataFrame([solution['summary']])
                df_summary.to_excel(writer, sheet_name='Résumé', index=False)
                
    @staticmethod
    def create_example_data():
        """Crée un exemple de données pour traitement de dossiers administratifs"""
        data = {
            "description": "Traitement de dossiers de demandes de permis",
            "optimization_mode": "minimize_stations",
            "cycle_time": 60,  # 60 minutes par dossier
            "max_stations": 10,
            
            "tasks": [
                {
                    "id": "T1",
                    "name": "Réception et enregistrement",
                    "duration": 8,
                    "complexity": 2,
                    "priority": 1,
                    "skills": ["bureautique"],
                    "resources": ["ordinateur", "scanner"],
                    "quality_level": 3
                },
                {
                    "id": "T2",
                    "name": "Vérification complétude dossier",
                    "duration": 12,
                    "complexity": 3,
                    "priority": 1,
                    "skills": ["bureautique", "réglementation"],
                    "resources": ["ordinateur"],
                    "quality_level": 4
                },
                {
                    "id": "T3",
                    "name": "Contrôle conformité réglementaire",
                    "duration": 20,
                    "complexity": 5,
                    "priority": 2,
                    "skills": ["réglementation", "expertise_juridique"],
                    "resources": ["ordinateur", "base_juridique"],
                    "quality_level": 5
                },
                {
                    "id": "T4",
                    "name": "Analyse technique du dossier",
                    "duration": 25,
                    "complexity": 5,
                    "priority": 2,
                    "skills": ["expertise_technique"],
                    "resources": ["ordinateur", "logiciel_cao"],
                    "quality_level": 5
                },
                {
                    "id": "T5",
                    "name": "Consultation services externes",
                    "duration": 15,
                    "complexity": 3,
                    "priority": 3,
                    "skills": ["communication"],
                    "resources": ["téléphone", "email"],
                    "quality_level": 3
                },
                {
                    "id": "T6",
                    "name": "Rédaction avis préliminaire",
                    "duration": 18,
                    "complexity": 4,
                    "priority": 3,
                    "skills": ["rédaction", "réglementation"],
                    "resources": ["ordinateur", "modèles_documents"],
                    "quality_level": 4
                },
                {
                    "id": "T7",
                    "name": "Validation hiérarchique",
                    "duration": 10,
                    "complexity": 3,
                    "priority": 4,
                    "skills": ["validation"],
                    "resources": ["ordinateur"],
                    "quality_level": 4
                },
                {
                    "id": "T8",
                    "name": "Notification au demandeur",
                    "duration": 7,
                    "complexity": 2,
                    "priority": 5,
                    "skills": ["bureautique", "communication"],
                    "resources": ["ordinateur", "imprimante"],
                    "quality_level": 3
                },
                {
                    "id": "T9",
                    "name": "Archivage et classement",
                    "duration": 5,
                    "complexity": 1,
                    "priority": 5,
                    "skills": ["bureautique"],
                    "resources": ["ordinateur", "scanner"],
                    "quality_level": 2
                }
            ],
            
            "precedences": [
                ["T1", "T2"],
                ["T2", "T3"],
                ["T2", "T4"],
                ["T3", "T5"],
                ["T4", "T5"],
                ["T5", "T6"],
                ["T6", "T7"],
                ["T7", "T8"],
                ["T8", "T9"]
            ],
            
            "incompatibilities": [
                ["T3", "T4"],  # Expertise juridique et technique sur postes différents
                ["T1", "T7"]   # Réception et validation sur postes différents
            ],
            
            "setup_times": [
                ["T2", "T3", 5],
                ["T3", "T6", 3],
                ["T6", "T7", 2]
            ],
            
            "stations": [
                {
                    "id": "S1",
                    "skills": ["bureautique", "communication"]
                },
                {
                    "id": "S2",
                    "skills": ["bureautique", "réglementation"]
                },
                {
                    "id": "S3",
                    "skills": ["réglementation", "expertise_juridique"]
                },
                {
                    "id": "S4",
                    "skills": ["expertise_technique"]
                },
                {
                    "id": "S5",
                    "skills": ["rédaction", "réglementation", "communication"]
                },
                {
                    "id": "S6",
                    "skills": ["validation", "réglementation"]
                }
            ]
        }
        
        return data
