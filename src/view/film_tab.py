from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QSizePolicy
from src.models.film import Film

from src.services.film_dm import FilmdataManager

from src.view.add_window import AddData


class FilmWidget(QWidget):
    def __init__(self, data_folder):
        super().__init__()
        
        self.dm = FilmdataManager(path=data_folder)
        self.films = self.dm.get_films()
        
        self.columns = ["Titre", "Note"]
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(self.columns)
        layout.addWidget(self.table)
        
        self.load_films()
        
        button = QPushButton("Add")
        button.setStyleSheet("background-color: green;")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.clicked.connect(self.open_add_window)
        
        layout.addWidget(button)
        
    def load_films(self):
        for film in self.films:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(film.titre))
            self.table.setItem(row, 1, QTableWidgetItem(str(film.note)))
    
    def add_film(self, film: Film):
        self.dm.add_film(film)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(film.titre))
        self.table.setItem(row, 1, QTableWidgetItem(str(film.note)))
    
    def open_add_window(self) :
        add_window = AddData(self.columns)
        add_window.exec_()
        data = add_window.get_data()
        
        films = Film()
        for col in self.columns :
            setattr(films, col.lower(), data.get(col))
        
        self.add_film(films)