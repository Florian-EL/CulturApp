from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QScrollArea, QWidget, \
    QGraphicsView, QGraphicsScene, QTableView, QTableWidget, QHeaderView, QTableWidgetItem, QSizePolicy, \
    QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor


class CulturApp(QWidget) :
    def __init__(self) :
        super().__init__()
        
        self.cultur_menu = ["Films", "Serie_film", "Series", "Romans", "Manga", "Webtoon", "Wattpad", "Music"]
        
        self.init_ui()
    
    def init_ui(self) :
        self.layout = QVBoxLayout()
        self.right_menu_layout = QVBoxLayout()
        self.window_layout = QHBoxLayout()
        self.stat_layout = QVBoxLayout()
        self.main_layout = QVBoxLayout()
        
        self.set_menu()
        self.set_stat()
        self.set_main()
        self.define_layout()
        
        self.setLayout(self.layout)
        
    def set_menu(self) :
        button_home = QPushButton("Home")
        button_home.setStyleSheet("background-color: red;")
        button_home.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        #TODO button_home.clicked.connect(self.set_main)
        self.right_menu_layout.addWidget(button_home)
        
        for menu in self.cultur_menu :
            button = QPushButton(menu)
            button.setStyleSheet("background-color: red;")
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            #TODO button.clicked.connect(getattr(self, f"set_{menu.lower()}"))
            self.right_menu_layout.addWidget(button)
    
    def set_main(self) :
        label1 = QLabel("main")
        label1.setStyleSheet("background-color: green;")
        self.main_layout.addWidget(label1)
    
    def set_stat(self) :
        label2 = QLabel("stat")
        label2.setStyleSheet("background-color: blue;")
        self.stat_layout.addWidget(label2)
        
    def define_layout(self) :
        self.stat_layout.addLayout(self.main_layout)
        self.window_layout.addLayout(self.right_menu_layout)
        self.window_layout.addLayout(self.stat_layout)
        
        self.layout.addLayout(self.window_layout)