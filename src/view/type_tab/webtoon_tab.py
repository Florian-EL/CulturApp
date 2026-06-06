from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QSizePolicy
from src.models.webtoon import Webtoon


from src.view.add_window import AddData
from src.view.del_window import DelData


class WebtoonWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        
        self.db = db
        self.data = self.db.get("webtoon", Webtoon)
        
        self.columns = ["Titre", "Note"]
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
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
        self.data = self.db.get("webtoon", Webtoon)
        self.table.setRowCount(0)  # Vide le tableau
        self.load()
    
    def set_data(self, data : Webtoon) :
        row = self.table.rowCount()
        self.table.insertRow(row)
        for i, col in enumerate(self.columns) :
            self.table.setItem(row, i, QTableWidgetItem(getattr(data, col.lower())))
    
    def load(self):
        for data in self.data:
            self.set_data(data)
    
    def add(self, data: Webtoon):
        self.db.add("webtoon", data)
        self.set_data(data)
    
    def open_add_window(self) :
        add_window = AddData(self.columns)
        add_window.exec_()
        new_data = add_window.get_data()
        
        data = Webtoon()
        for col in self.columns :
            setattr(data, col.lower(), new_data.get(col))
        
        self.add(data)
    
    def open_del_window(self) :
        del_window = DelData()
        del_window.exec_()
        data = del_window.get_data()
        
        self.db.delete("webtoon", Webtoon(id=int(data)))
        
        self.refresh()