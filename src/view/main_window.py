from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QScrollArea, QWidget, \
    QGraphicsView, QGraphicsScene, QTableView, QTableWidget, QHeaderView, QTableWidgetItem, QSizePolicy, \
    QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor

from src.view.home_tab import HomeWidget
from src.view.film_tab import FilmWidget
from src.view.serie_film_tab import SerieFilmWidget
from src.services.database_manager import DatabaseManager
from src.view.settings_dialog import SettingsDialog
from src.utils import clear_layout
from src.models.film import Film


class CulturApp(QWidget) :
    def __init__(self, data_folder) :
        super().__init__()
        
        self.data_folder = data_folder
        self.cultur_menu = ["Films", "Serie_films"]#, "Series", "Romans", "Manga", "Webtoon", "Wattpad", "Music"]
        
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
        self.db = DatabaseManager(self.data_folder)
        
        self.menu_films = FilmWidget(self.db)
        self.menu_serie_films = SerieFilmWidget(self.db)

        self.stack.addWidget(self.home_widget)
        self.stack.addWidget(self.menu_films)
        self.stack.addWidget(self.menu_serie_films)
        
        # Rafraîchir les données quand on change d'onglet
        self.stack.currentChanged.connect(self.on_tab_changed)
        
        self.set_window()
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
            button.clicked.connect(lambda checked=False, m=menu: self.stack.setCurrentWidget(getattr(self, f"menu_{m.lower()}")))
            self.right_menu_layout.addWidget(button)
        
        # Ajouter un bouton Paramètres
        self.right_menu_layout.addStretch()
        button_settings = QPushButton("Paramètres")
        button_settings.setStyleSheet("background-color: blue;")
        button_settings.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_settings.clicked.connect(self.open_settings)
        self.right_menu_layout.addWidget(button_settings)
    
    def on_tab_changed(self, index):
        """Rafraîchit l'onglet quand on change de page"""
        widget = self.stack.currentWidget()
        if hasattr(widget, 'refresh_films'):
            widget.refresh_films()
        elif hasattr(widget, 'refresh_serie_films'):
            widget.refresh_serie_films()
    
    def open_settings(self):
        """Ouvre le dialogue des paramètres"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()
    
    def define_layout(self) :
        self.stat_layout.addLayout(self.main_layout)
        self.window_layout.addLayout(self.right_menu_layout)
        self.window_layout.addLayout(self.stat_layout)
        
        self.layout.addLayout(self.window_layout)
    

