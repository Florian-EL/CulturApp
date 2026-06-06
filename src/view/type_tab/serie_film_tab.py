from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QSizePolicy
from src.models.serie_film import SerieFilm


from src.view.add_window import AddData
from src.view.del_window import DelData


class SerieFilmWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        
        self.db = db
        self.data = self.db.get("serie_film", SerieFilm)
        
        self.columns = ["Nom_serie", "Film", "Titre", "Type", "Genre", "VO", "Cinema", 
                        "Updated", "Etat", "Annee_vu", "Nb_vu", "Note"]
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        layout.addWidget(self.table)
        
        self.load()
        
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Add")
        add_button.setStyleSheet("background-color: green;")
        add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        add_button.clicked.connect(self.open_add_window)
        
        del_button = QPushButton("Del")
        del_button.setStyleSheet("background-color: red;")
        del_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        del_button.clicked.connect(self.open_del_window)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(del_button)
        
        layout.addLayout(buttons_layout)
    
    def showEvent(self, event):
        """Appelé quand le widget devient visible"""
        super().showEvent(event)
        self.refresh()
        
    def refresh(self):
        """Rafraîchit les données depuis la base de données"""
        self.data = self.db.get("serie_film", SerieFilm)
        self.table.setRowCount(0)  # Vide le tableau
        self.load()
    
    def set_data(self, data : SerieFilm) :
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(data.nom_serie))
        self.table.setItem(row, 1, QTableWidgetItem(data.film))
        self.table.setItem(row, 2, QTableWidgetItem(data.titre))
        self.table.setItem(row, 3, QTableWidgetItem(data.type))
        self.table.setItem(row, 4, QTableWidgetItem(data.genre))
        self.table.setItem(row, 5, QTableWidgetItem(data.vo))
        self.table.setItem(row, 6, QTableWidgetItem(data.cinema))
        self.table.setItem(row, 7, QTableWidgetItem(data.updated))
        self.table.setItem(row, 8, QTableWidgetItem(data.etat))
        self.table.setItem(row, 9, QTableWidgetItem(data.annee_vu))
        self.table.setItem(row, 10, QTableWidgetItem(data.nb_vu))
        self.table.setItem(row, 11, QTableWidgetItem(str(data.note)))
    
    def load(self):
        for data in self.data:
            self.set_data(data)
    
    def add(self, data: SerieFilm):
        self.db.add("serie_film", data)
        self.set_data(data)
    
    def open_add_window(self) :
        add_window = AddData(self.columns)
        add_window.exec_()
        new_data = add_window.get_data()
        
        data = SerieFilm()
        for col in self.columns :
            setattr(data, col.lower(), new_data.get(col))
        
        self.add(data)
    
    def open_del_window(self) :
        del_window = DelData()
        del_window.exec_()
        data = del_window.get_data()
        
        self.db.delete("serie_film", SerieFilm(id=int(data)))
        
        self.refresh()