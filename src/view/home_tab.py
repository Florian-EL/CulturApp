from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class HomeWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Accueil"))