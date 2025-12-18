from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget

class TransportWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Equilibrage de Chaîne - Traitement Dossiers")
        self.resize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        label = QLabel("Bienvenue dans le module d'Optimisation des flux")
        layout.addWidget(label)
