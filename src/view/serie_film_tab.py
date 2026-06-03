from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QSizePolicy
from src.models.serie_film import SerieFilm


from src.view.add_window import AddData


class SerieFilmWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        
        self.db = db
        self.data = self.db.get("serie_film", SerieFilm)
        
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
        self.data = self.db.get("serie_film", SerieFilm)
        self.table.setRowCount(0)  # Vide le tableau
        self.load()
    
    def load(self):
        for data in self.data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(data.titre))
            self.table.setItem(row, 1, QTableWidgetItem(str(data.note)))
    
    def add(self, data: SerieFilm):
        self.db.add("serie_film", data)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(data.titre))
        self.table.setItem(row, 1, QTableWidgetItem(str(data.note)))
    
    def open_add_window(self) :
        add_window = AddData(self.columns)
        add_window.exec_()
        data = add_window.get_data()
        
        data = SerieFilm()
        for col in self.columns :
            setattr(data, col.lower(), new_data.get(col))
        
        self.add(data)