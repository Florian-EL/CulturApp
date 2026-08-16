from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel

class DelData(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Data")

        self.layout = QVBoxLayout()

        self.label = QLabel("ID à supprimer :")
        self.layout.addWidget(self.label)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("id")
        self.layout.addWidget(self.id_input)

        self.delete_button = QPushButton("Supprimer")
        self.delete_button.clicked.connect(self.accept)
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

    def get_data(self):
        return self.id_input.text()