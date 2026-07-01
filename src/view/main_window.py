from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMenuBar, QLabel, QScrollArea, QWidget, \
    QGraphicsView, QGraphicsScene, QTableView, QTableWidget, QHeaderView, QTableWidgetItem, QSizePolicy, \
    QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QFileDialog, QAction
from PyQt5.QtCore import Qt, QRectF

from pandas import read_csv
import json

from src.models.serie import Serie

from src.view.home_tab import HomeWidget

from src.view.type_tab.film_tab import FilmWidget
from src.view.type_tab.serie_film_tab import SerieFilmWidget
# from src.view.type_tab.serie_tab import SerieWidget
from src.view.type_tab.roman_tab import RomanWidget
from src.view.type_tab.manga_tab import MangaWidget
from src.view.type_tab.webtoon_tab import WebtoonWidget
from src.view.type_tab.wattpad_tab import WattpadWidget


from src.view.TypeTab import TypeWidget

from src.services.database_manager import DatabaseManager
from src.view.settings_dialog import SettingsDialog
from src.services.config_manager import ConfigManager


class CulturApp(QWidget) :
    def __init__(self) :
        super().__init__()

        config_manager = ConfigManager()
        self.data_folder = config_manager.get_data_folder()

        with open(config_manager.get_config_file(), 'r', encoding="utf-8") as file :
            self.config = json.load(file)
        
        self.cultur_menu = ["Films", "Serie_films", "Series", "Romans", "Mangas", "Webtoons", "Wattpads"]
        
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
        self.menu_series = TypeWidget(self.db, "serie", Serie, self.config["columns"]["serie"], self.config["hidden_columns"]["serie"])
        self.menu_romans = RomanWidget(self.db)
        self.menu_mangas = MangaWidget(self.db)
        self.menu_webtoons = WebtoonWidget(self.db)
        self.menu_wattpads = WattpadWidget(self.db)

        
        menu_bar = QMenuBar()
        self.layout.setMenuBar(menu_bar)
        self.menu_widget = menu_bar.addMenu("File")        
        self.create_import_menu()
        
        
        #self.stack.addWidget(self.menu_widget)

        self.stack.addWidget(self.home_widget)
        self.stack.addWidget(self.menu_films)
        self.stack.addWidget(self.menu_serie_films)
        self.stack.addWidget(self.menu_series)
        self.stack.addWidget(self.menu_romans)
        self.stack.addWidget(self.menu_mangas)
        self.stack.addWidget(self.menu_webtoons)
        self.stack.addWidget(self.menu_wattpads)
        
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
    
    def on_tab_changed(self):
        """Rafraîchit l'onglet quand on change de page"""
        widget = self.stack.currentWidget()
        widget.refresh()
    
    def open_settings(self):
        """Ouvre le dialogue des paramètres"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()
    
    def define_layout(self) :
        self.stat_layout.addLayout(self.main_layout)
        self.window_layout.addLayout(self.right_menu_layout)
        self.window_layout.addLayout(self.stat_layout)
        
        self.layout.addLayout(self.window_layout)
    

    def create_import_menu(self):
        action_csv = QAction("Importer CSV", self)
        action_csv.triggered.connect(self.import_csv)
        self.menu_widget.addAction(action_csv)
        

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,"Importer un fichier CSV","","CSV (*.csv)")
        if file_path != "" :
            widget = self.stack.currentWidget()
            df = read_csv(file_path, delimiter=";")
            widget.add_import(df)