from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QScrollArea, QWidget, \
    QGraphicsView, QGraphicsScene, QTableView, QTableWidget, QHeaderView, QTableWidgetItem, QSizePolicy, \
    QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor

from src.view.home_tab import HomeWidget
from src.view.film_tab import FilmWidget
from src.utils import clear_layout


class CulturApp(QWidget) :
    def __init__(self) :
        super().__init__()
        
        self.cultur_menu = ["Films"]#, "Serie_film", "Series", "Romans", "Manga", "Webtoon", "Wattpad", "Music"]
        
        self.init_ui()
    
    def init_ui(self) :
        self.layout = QVBoxLayout()
        self.right_menu_layout = QVBoxLayout()
        self.window_layout = QHBoxLayout()
        self.stat_layout = QVBoxLayout()
        self.main_layout = QVBoxLayout()
        
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.home_widget = HomeWidget()
        self.menu_films = FilmWidget()

        self.stack.addWidget(self.home_widget)
        self.stack.addWidget(self.menu_films)
        
        self.set_window()
        # self.set_stat()
        # self.set_main()
        self.define_layout()
        
        self.setLayout(self.layout)
        
    def set_window(self) :
        button_home = QPushButton("Home")
        button_home.setStyleSheet("background-color: red;")
        button_home.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        button_home.clicked.connect(lambda: self.stack.setCurrentWidget(self.home_widget))
        self.right_menu_layout.addWidget(button_home)
        
        for menu in self.cultur_menu :
            button = QPushButton(menu)
            button.setStyleSheet("background-color: red;")
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            button.clicked.connect(lambda: self.stack.setCurrentWidget(getattr(self, f"menu_{menu.lower()}")))
            self.right_menu_layout.addWidget(button)
        
        button = QPushButton("Add")
        button.setStyleSheet("background-color: red;")
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        button.clicked.connect(lambda: self.stack.setCurrentWidget(self.menu_films.update_count(10)))
        self.right_menu_layout.addWidget(button)
    
    def define_layout(self) :
        self.stat_layout.addLayout(self.main_layout)
        self.window_layout.addLayout(self.right_menu_layout)
        self.window_layout.addLayout(self.stat_layout)
        
        self.layout.addLayout(self.window_layout)