from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMenuBar, QLabel, QScrollArea, QWidget, \
    QGraphicsView, QGraphicsScene, QTableView, QTableWidget, QHeaderView, QTableWidgetItem, QSizePolicy, \
    QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QFileDialog, QAction
from PyQt5.QtCore import Qt, QRectF

from pandas import read_csv
import json

from src.models.film import Film
from src.models.serie_film import SerieFilm
from src.models.serie import Serie
from src.models.roman import Roman
from src.models.manga import Manga
from src.models.wattpad import Wattpad
from src.models.webtoon import Webtoon

from src.view.home_tab import HomeWidget
from src.view.TypeTab import TypeWidget

from src.services.database_manager import DatabaseManager
from src.view.settings_dialog import SettingsDialog
from src.services.config_manager import ConfigManager


class CulturApp(QWidget) :
    def __init__(self, test=False) :
        super().__init__()
        self.test = test
        config_manager = ConfigManager(test)
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

        self.db = DatabaseManager(self.data_folder)
        self.home_widget = HomeWidget(self.db)
        initial_sorts = self.config.get("initial_sort", {})
        
        self.menu_films = TypeWidget(self.db, "film", Film, self.config["columns"]["film"], self.config["hidden_columns"]["film"], self.data_folder, initial_sort_rules=initial_sorts.get("film", []))
        self.menu_serie_films = TypeWidget(self.db, "serie_film", SerieFilm, self.config["columns"]["serie_film"], self.config["hidden_columns"]["serie_film"], self.data_folder, initial_sort_rules=initial_sorts.get("serie_film", []))
        self.menu_series = TypeWidget(self.db, "serie", Serie, self.config["columns"]["serie"], self.config["hidden_columns"]["serie"], self.data_folder, initial_sort_rules=initial_sorts.get("serie", []))
        self.menu_romans = TypeWidget(self.db, "roman", Roman, self.config["columns"]["roman"], self.config["hidden_columns"]["roman"], self.data_folder, initial_sort_rules=initial_sorts.get("roman", []))
        self.menu_mangas = TypeWidget(self.db, "manga", Manga, self.config["columns"]["manga"], self.config["hidden_columns"]["manga"], self.data_folder, initial_sort_rules=initial_sorts.get("manga", []))
        self.menu_webtoons = TypeWidget(self.db, "webtoon", Webtoon, self.config["columns"]["webtoon"], self.config["hidden_columns"]["webtoon"], self.data_folder, initial_sort_rules=initial_sorts.get("webtoon", []))
        self.menu_wattpads = TypeWidget(self.db, "wattpad", Wattpad, self.config["columns"]["wattpad"], self.config["hidden_columns"]["wattpad"], self.data_folder, initial_sort_rules=initial_sorts.get("wattpad", []))
        
        menu_bar = QMenuBar()
        self.layout.setMenuBar(menu_bar)
        self.menu_widget = menu_bar.addMenu("File")        
        self.create_import_menu()
        
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
        settings_dialog = SettingsDialog(self.test, self)
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