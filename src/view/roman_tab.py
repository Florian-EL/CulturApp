from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QSizePolicy
from src.models.roman import Roman


from src.view.add_window import AddData


class RomanWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        
        self.db = db
        self.roman = self.db.get("roman", Roman)
        
        self.columns = ["Titre", "Note"]
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(self.columns)
        layout.addWidget(self.table)
        
        self.load_roman()
        
        button = QPushButton("Add")
        button.setStyleSheet("background-color: green;")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.clicked.connect(self.open_add_window)
        
        layout.addWidget(button)
    
    def showEvent(self, event):
        """Appelé quand le widget devient visible"""
        super().showEvent(event)
        self.refresh_roman()
        
    def refresh_roman(self):
        """Rafraîchit les données depuis la base de données"""
        self.roman = self.db.get("roman", Roman)
        self.table.setRowCount(0)  # Vide le tableau
        self.load_roman()
    
    def load_roman(self):
        for roman in self.roman:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(roman.titre))
            self.table.setItem(row, 1, QTableWidgetItem(str(roman.note)))
    
    def add_serie_film(self, roman: Roman):
        self.db.add("roman", roman)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(roman.titre))
        self.table.setItem(row, 1, QTableWidgetItem(str(roman.note)))
    
    def open_add_window(self) :
        add_window = AddData(self.columns)
        add_window.exec_()
        data = add_window.get_data()
        
        roman = Roman()
        for col in self.columns :
            setattr(roman, col.lower(), data.get(col))
        
        self.add_serie_film(roman)