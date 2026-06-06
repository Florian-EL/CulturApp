from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QSizePolicy
from src.models.serie import Serie


from src.view.add_window import AddData
from src.view.del_window import DelData


class SerieWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        
        self.db = db
        self.data = self.db.get("serie", Serie)
        
        self.columns = ["Titre", "Type", "Genre", "VO", 
                        "Updated", "Etat", "Nb_saison", "Nb_ep_vu",
                        "Nb_ep_voir", "Nb_ep_total", "Nb_vu", "Note", 
                        "Sortie", "S1_vu", "S1_tot", "S2_vu", "S2_tot",
                        "S3_vu", "S3_tot", "S4_vu", "S4_tot", 
                        "S5_vu", "S5_tot", "S6_vu", "S6_tot",
                        "S7_vu", "S7_tot", "S8_vu", "S8_tot"]
        #Nombre épisodes à voir Nombre épisodes total
        
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
        self.data = self.db.get("serie", Serie)
        self.table.setRowCount(0)  # Vide le tableau
        self.load()
    
    def calculate(self, data: Serie):
        nb_saison = 0
        data.nb_ep_total = 0
        data.nb_ep_vu = 0
        for col in self.columns:
            if col.endswith("_tot"):
                if getattr(data, col.lower(), 0) != "":
                    nb_saison += 1
                    data.nb_ep_total += int(getattr(data, col.lower(), 0))
            if col.endswith("_vu"):
                if getattr(data, col.lower(), 0) != "":
                    data.nb_ep_vu += int(getattr(data, col.lower(), 0))
        
        data.nb_saison = nb_saison
        data.nb_ep_voir = data.nb_ep_total - data.nb_ep_vu
        
        return data
    
    def set_data(self, data : Serie) :
        row = self.table.rowCount()
        self.table.insertRow(row)
        for i, col in enumerate(self.columns) :
            self.table.setItem(row, i, QTableWidgetItem(str(getattr(data, col.lower()))))
    
    def load(self):
        for data in self.data:
            self.set_data(data)
    
    def add(self, data: Serie):
        cal_data = self.calculate(data)
        self.db.add("serie", cal_data)
        self.set_data(cal_data)
    
    def open_add_window(self) :
        colonne = self.columns.copy()
        col_idx = self.columns.index('Nb_ep_total')
        colonne.pop(col_idx)
        col_idx = self.columns.index('Nb_ep_voir')
        colonne.pop(col_idx)
        col_idx = self.columns.index('Nb_ep_vu')
        colonne.pop(col_idx)
        col_idx = self.columns.index('Nb_saison')
        colonne.pop(col_idx)
        
        add_window = AddData(colonne)
        add_window.exec_()
        new_data = add_window.get_data()
        
        data = Serie()
        for col in self.columns :
            setattr(data, col.lower(), new_data.get(col))
        
        self.add(data)
    
    def open_del_window(self) :
        del_window = DelData()
        del_window.exec_()
        data = del_window.get_data()
        
        self.db.delete("serie", Serie(id=int(data)))
        
        self.refresh()