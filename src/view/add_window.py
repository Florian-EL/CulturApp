from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton

class AddData(QDialog) :
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Data")
        self.layout = QVBoxLayout()
        
        self.columns = columns
        
        self.inputs = {}
        
        for col in self.columns :
            input_field = QLineEdit()
            input_field.setPlaceholderText(col)
            self.inputs[col] = input_field
            self.layout.addWidget(input_field)
        

        self.add_button = QPushButton("Ajouter")
        self.add_button.clicked.connect(self.accept)
        self.layout.addWidget(self.add_button)
        
        self.setLayout(self.layout)
        
    def get_data(self) :
        data = {}
        
        for col in self.columns :
            widget = self.inputs.get(col)
            data[col] = widget.text()
        
        return data
