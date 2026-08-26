import json

from pandas import read_csv
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.film import Film
from src.models.manga import Manga
from src.models.roman import Roman
from src.models.serie import Serie
from src.models.serie_film import SerieFilm
from src.models.wattpad import Wattpad
from src.models.webtoon import Webtoon
from src.services.config_manager import ConfigManager
from src.services.database_manager import DatabaseManager
from src.view.citation_widget import CitationWidget
from src.view.home_tab import HomeWidget
from src.view.library_widget import LibraryWidgets
from src.view.settings_dialog import SettingsDialog
from src.view.TypeTab import TypeWidget


class CulturApp(QWidget) :
    def __init__(self, test=False) :
        super().__init__()
        self.test = test
        config_manager = ConfigManager(test)
        self.data_folder = config_manager.get_data_folder()

        with open(config_manager.get_config_file(), 'r', encoding="utf-8") as file :
            self.config = json.load(file)
        
        self.cultur_menu = [
            ("Citations", "citation"),
            ("Films", "film"),
            ("Serie_films", "serie_film"),
            ("Series", "serie"),
            ("Romans", "roman"),
            ("Mangas", "manga"),
            ("Webtoons", "webtoon"),
            ("Wattpads", "wattpad"),
        ]
        self.initial_sorts = self.config.get("initial_sort", {})
        self._type_widgets = {}
        self._type_widget_specs = {}
        self._background_load_timer = None
        self._background_loaded = False
        
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
        self._type_widget_specs = {
            "film": {
                "table_name": "film",
                "model_cls": Film,
                "columns": self.config["columns"]["film"],
                "hidden_columns": self.config["hidden_columns"]["film"],
            },
            "serie_film": {
                "table_name": "serie_film",
                "model_cls": SerieFilm,
                "columns": self.config["columns"]["serie_film"],
                "hidden_columns": self.config["hidden_columns"]["serie_film"],
            },
            "serie": {
                "table_name": "serie",
                "model_cls": Serie,
                "columns": self.config["columns"]["serie"],
                "hidden_columns": self.config["hidden_columns"]["serie"],
            },
            "roman": {
                "table_name": "roman",
                "model_cls": Roman,
                "columns": self.config["columns"]["roman"],
                "hidden_columns": self.config["hidden_columns"]["roman"],
            },
            "manga": {
                "table_name": "manga",
                "model_cls": Manga,
                "columns": self.config["columns"]["manga"],
                "hidden_columns": self.config["hidden_columns"]["manga"],
            },
            "webtoon": {
                "table_name": "webtoon",
                "model_cls": Webtoon,
                "columns": self.config["columns"]["webtoon"],
                "hidden_columns": self.config["hidden_columns"]["webtoon"],
            },
            "wattpad": {
                "table_name": "wattpad",
                "model_cls": Wattpad,
                "columns": self.config["columns"]["wattpad"],
                "hidden_columns": self.config["hidden_columns"]["wattpad"],
            },
        }
        
        self.library_widgets = LibraryWidgets(self.db, self.data_folder)
        
        self.stack.addWidget(self.home_widget)
        self.stack.addWidget(self.library_widgets)
        
        # Rafraîchir les données quand on change d'onglet
        self.stack.currentChanged.connect(self.on_tab_changed)
        
        self.set_window()
        self.define_layout()
        
        self.setLayout(self.layout)
        self._schedule_background_preload()
        
    def set_window(self) :
        button_home = QPushButton("Home")
        button_home.setStyleSheet("background-color: red;")
        button_home.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        button_home.clicked.connect(lambda: self.stack.setCurrentWidget(self.home_widget))
        self.right_menu_layout.addWidget(button_home)
        
        button_library = QPushButton("Library")
        button_library.setStyleSheet("background-color: red;")
        button_library.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        button_library.clicked.connect(lambda: self.stack.setCurrentWidget(self.library_widgets))
        self.right_menu_layout.addWidget(button_library)
        
        for menu_name, menu_key in self.cultur_menu:
            button = QPushButton(menu_name)
            button.setStyleSheet("background-color: red;")
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            button.clicked.connect(lambda checked=False, key=menu_key: self._show_type_widget(key))
            self.right_menu_layout.addWidget(button)
        
        
        # Ajouter un bouton Paramètres
        self.right_menu_layout.addStretch()
        
        self.create_import_menu()
        self.create_settings_button()
    
    def _schedule_background_preload(self):
        if self._background_loaded:
            return
        if self._background_load_timer is None:
            self._background_load_timer = QTimer(self)
            self._background_load_timer.setSingleShot(True)
            self._background_load_timer.timeout.connect(self._background_preload)
        self._background_load_timer.start(150)

    def _background_preload(self):
        if self._background_loaded:
            return
        self._background_loaded = True
        first_key = next(iter(self._type_widget_specs.keys()), None)
        if first_key is None:
            return
        self._show_type_widget(first_key, preload=True)

    def _show_type_widget(self, key, preload=False):
        if key == "citation":
            widget = self._type_widgets.get(key)
            if widget is None:
                widget = CitationWidget(
                    self.db,
                    self.config["columns"]["citation"],
                    self.data_folder,
                    self.initial_sorts.get("citation", []),
                    parent=self,
                )
                self._type_widgets[key] = widget
                self.stack.addWidget(widget)
            if not preload:
                self.stack.setCurrentWidget(widget)
            return

        widget = self._type_widgets.get(key)
        if widget is None:
            spec = self._type_widget_specs[key]
            field_options = self.config.get("field_options", {})
            widget = TypeWidget(
                self.db,
                spec["table_name"],
                spec["model_cls"],
                spec["columns"],
                spec["hidden_columns"],
                self.data_folder,
                initial_sort_rules=self.initial_sorts.get(spec["table_name"], []),
                field_options=field_options,
            )
            self._type_widgets[key] = widget
            self.stack.addWidget(widget)

        if not preload:
            self.stack.setCurrentWidget(widget)

    def on_tab_changed(self):
        """Rafraîchit l'onglet seulement si ce widget a déjà été chargé."""
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
        action_csv = QPushButton("Importer CSV", self)
        action_csv.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        action_csv.clicked.connect(self.import_csv)
        self.right_menu_layout.addWidget(action_csv)
        
    def create_settings_button(self):
        button_settings = QPushButton("Paramètres")
        button_settings.setStyleSheet("background-color: blue;")
        button_settings.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_settings.clicked.connect(self.open_settings)
        self.right_menu_layout.addWidget(button_settings)

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,"Importer un fichier CSV","","CSV (*.csv)")
        if file_path != "" :
            widget = self.stack.currentWidget()
            df = read_csv(file_path, delimiter=";")
            widget.add_import(df)