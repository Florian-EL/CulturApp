from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QSizePolicy
from src.models.serie_film import SerieFilm


from src.view.add_window import AddData


class SerieFilmWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        
        self.db = db
        self.serie_films = self.db.get_serie_films()
        
        self.columns = ["Titre", "Note"]
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(self.columns)
        layout.addWidget(self.table)
        
        self.load_serie_films()
        
        button = QPushButton("Add")
        button.setStyleSheet("background-color: green;")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.clicked.connect(self.open_add_window)
        
        layout.addWidget(button)
    
    def showEvent(self, event):
        """Appelé quand le widget devient visible"""
        super().showEvent(event)
        self.refresh_serie_films()
        
    def refresh_serie_films(self):
        """Rafraîchit les données depuis la base de données"""
        self.serie_films = self.db.get_serie_films()
        self.table.setRowCount(0)  # Vide le tableau
        self.load_serie_films()
    
    def load_serie_films(self):
        for film in self.serie_films:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(film.titre))
            self.table.setItem(row, 1, QTableWidgetItem(str(film.note)))
    
    def add_serie_film(self, film: SerieFilm):
        self.db.add_serie_film(film)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(film.titre))
        self.table.setItem(row, 1, QTableWidgetItem(str(film.note)))
    
    def open_add_window(self) :
        add_window = AddData(self.columns)
        add_window.exec_()
        data = add_window.get_data()
        
        films = SerieFilm()
        for col in self.columns :
            setattr(films, col.lower(), data.get(col))
        
        self.add_serie_film(films)