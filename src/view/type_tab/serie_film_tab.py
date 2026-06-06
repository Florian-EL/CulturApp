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
        self.col_aff = self.columns.copy()[2:]
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.col_aff))
        self.table.setHorizontalHeaderLabels(self.col_aff)
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
        for i, col in enumerate(self.col_aff) :
            self.table.setItem(row, i, QTableWidgetItem(getattr(data, col.lower())))
    
    def load(self):
        for data in self.data:
            self.set_data(data)
    
    def add(self, data: SerieFilm):
        self.db.add("serie_film", data)
        self.set_data(data)
    
    def open_add_window(self) :
        col_idx = self.columns.index('Titre')
        colonne = self.columns.copy()
        colonne.pop(col_idx)
        add_window = AddData(colonne)
        add_window.exec_()
        new_data = add_window.get_data()
        new_data['Titre'] = new_data['Nom_serie'] + " - " + new_data['Film']
        
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