from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QSizePolicy
from src.models.film import Film


from src.view.add_window import AddData


class FilmWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        
        self.db = db
        self.data = self.db.get("film", Film)
        
        self.columns = ["Titre", "Note"]
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(self.columns)
        layout.addWidget(self.table)
        
        self.load()
        
        button = QPushButton("Add")
        button.setStyleSheet("background-color: green;")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.clicked.connect(self.open_add_window)
        
        layout.addWidget(button)
    
    def showEvent(self, event):
        """Appelé quand le widget devient visible"""
        super().showEvent(event)
        self.refresh()
        
    def refresh(self):
        """Rafraîchit les données depuis la base de données"""
        self.data = self.db.get("film", Film)
        self.table.setRowCount(0)  # Vide le tableau
        self.load()
    
    def load(self):
        for data in self.data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(data.titre))
            self.table.setItem(row, 1, QTableWidgetItem(str(data.note)))
    
    def add(self, data: Film):
        self.db.add("film", data)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(data.titre))
        self.table.setItem(row, 1, QTableWidgetItem(str(data.note)))
    
    def open_add_window(self) :
        add_window = AddData(self.columns)
        add_window.exec_()
        new_data = add_window.get_data()
        
        data = Film()
        for col in self.columns :
            setattr(data, col.lower(), new_data.get(col))
        
        self.add_film(data)