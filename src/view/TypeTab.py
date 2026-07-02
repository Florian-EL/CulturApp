from dataclasses import fields

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, \
                            QTableWidgetItem, QPushButton, QSizePolicy, QDialog, QLabel, QMessageBox, QTabWidget
import pandas as pd

from src.view.add_window import AddData
from src.view.del_window import DelData
from src.view.edit_window import EditData
from src.view.gallery_widget import GalleryWidget, sanitize_filename
from pathlib import Path


class TypeWidget(QWidget):
    def __init__(self, db, table_name, model_cls, columns, hidden_columns, data_folder):
        super().__init__()
        
        self.db = db
        self.table_name = table_name
        self.model_cls = model_cls
        self.columns = columns
        self.hidden_columns = hidden_columns
        self.data_folder = data_folder

        layout = QVBoxLayout(self)

        # Create tabs: Table and Gallery
        self.tab_widget = QTabWidget()

        # Table tab
        table_page = QWidget()
        table_layout = QVBoxLayout(table_page)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns) + 1)
        self.table.setHorizontalHeaderLabels([""] + self.columns)
        table_layout.addWidget(self.table)

        self._load_data()
        self.load()

        # Buttons moved to shared area below tabs

        self.tab_widget.addTab(table_page, "Table")

        # Gallery tab
        self.gallery = GalleryWidget(self.db, self.table_name, self.model_cls, self.columns, self.data_folder, parent=self)
        self.tab_widget.addTab(self.gallery, "Gallery")

        # Refresh gallery when switching to that tab
        self.tab_widget.currentChanged.connect(self.on_subtab_changed)

        layout.addWidget(self.tab_widget)

        # Shared buttons visible on both tabs
        shared_buttons = QHBoxLayout()
        add_button = QPushButton("Add")
        add_button.setStyleSheet("background-color: green;")
        add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        add_button.clicked.connect(self.open_add_window)

        del_button = QPushButton("Del")
        del_button.setStyleSheet("background-color: red;")
        del_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        del_button.clicked.connect(self.open_del_window)

        shared_buttons.addWidget(add_button)
        shared_buttons.addWidget(del_button)
        layout.addLayout(shared_buttons)
    
    def showEvent(self, event):
        """Appelé quand le widget devient visible"""
        super().showEvent(event)
        self.refresh()
        
    def _load_data(self):
        self.data = [self.calculate(data) for data in self.db.get(self.table_name, self.model_cls)]

    def refresh(self):
        """Rafraîchit les données depuis la base de données"""
        self._load_data()
        self.table.setRowCount(0)  # Vide le tableau
        self.load()
        # Refresh gallery view as well
        try:
            if hasattr(self, 'gallery'):
                self.gallery.refresh()
        except Exception:
            pass

    def on_subtab_changed(self, index):
        # If switching to gallery tab, refresh its content
        try:
            if self.tab_widget.tabText(index) == "Gallery":
                self.gallery.refresh()
        except Exception:
            pass
    
    def calculate(self, data):
        if self.table_name == "manga" :
            data.nb_ep_vu = data.ep_act
        
        data.nb_ep_res = int(data.nb_ep_tot) - int(data.nb_ep_vu)
        data.etat = "FINI" if data.note != "" else "EN COURS"

        if self.table_name == "serie" :
            nb_saison = 0
            data.nb_ep_tot = 0
            data.nb_ep_vu = 0
            for col in self.columns:
                if col.endswith("_tot"):
                    if getattr(data, col.lower(), 0) != "":
                        nb_saison += 1
                        data.nb_ep_tot += int(getattr(data, col.lower(), 0))
                if col.endswith("_vu") and col.lower() not in ["nb_ep_vu", "nb_vu"] :
                    if getattr(data, col.lower(), 0) != "":
                        data.nb_ep_vu += int(getattr(data, col.lower(), 0))
            data.nb_saison = nb_saison
        
        if self.table_name in ["film", "serie_film"] :
            if data.updated == "PAS SORTI" :
                data.nb_ep_tot = 0
                data.nb_vu = 0
                data.nb_ep_vu= 0
            elif data.etat == "EN COURS" :
                data.nb_ep_tot = 1
                data.nb_ep_vu = 0
                data.nb_vu = 0
            elif data.etat == "FINI" :
                try :
                    data.nb_ep_vu = len(data.annee_vu.split(","))
                except AttributeError :
                    data.nb_ep_vu = 0 if data.annee_vu == 0 else 1
                data.nb_ep_tot = data.nb_ep_vu
                data.nb_vu = data.nb_vu
        
        if self.table_name == "serie_film" :
            data.titre = data.nom_serie + " - " + data.film
        
        if data.nb_ep_tot == 0 :
            data.updated = "PAS SORTI"
            data.etat = ""
        elif data.nb_ep_tot > data.nb_ep_vu :
            data.etat = "EN COURS"
        elif data.nb_ep_tot == data.nb_ep_vu :
            data.etat == "FINI"
        
        if self.table_name == "manga" : 
            data.nb_ep_vu = int(data.ep_act) - int(data.ep_deb)
            data.nb_ep_res = int(data.nb_ep_tot) - int(data.ep_act)
        
        
        return data
    
    def add_import(self, df: pd.DataFrame) :
        df_columns = set(df.columns)
        required_columns = set([col.lower() for col in self.columns])
        
        if not required_columns.issubset(df_columns):
            missing = required_columns - df_columns
            QMessageBox.warning(self, "Erreur", f"Colonnes manquantes : {missing}")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Importer des données")
        dialog.setGeometry(100, 100, 400, 150)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Importer {len(df)} série(s).\nVoulez-vous remplacer toutes les données existantes ?"))
        
        buttons_layout = QHBoxLayout()
        
        replace_button = QPushButton("Remplacer")
        replace_button.setStyleSheet("background-color: orange;")
        replace_button.clicked.connect(lambda: self.import_and_replace(df, dialog))
        
        add_button = QPushButton("Ajouter")
        add_button.setStyleSheet("background-color: green;")
        add_button.clicked.connect(lambda: self._import_add(df, dialog))
        
        cancel_button = QPushButton("Annuler")
        cancel_button.setStyleSheet("background-color: gray;")
        cancel_button.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(replace_button)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        dialog.exec_()
    
    def import_and_replace(self, df: pd.DataFrame, dialog: QDialog):
        for data in self.data:
            self.db.delete(self.table_name, self.model_cls(id=data.id))
        
        self._import_add(df, dialog)
    
    def _import_add(self, df: pd.DataFrame, dialog: QDialog):
        for _, row in df.iterrows():
            data = self.model_cls()
            for col in self.columns:
                col_lower = col.lower()
                if col_lower in df.columns:
                    value = row[col_lower]
                    if pd.isna(value):
                        value = ""
                    setattr(data, col_lower, value)
            
            data = self.calculate(data)
            self.db.add(self.table_name, data)
        
        self.refresh()
        dialog.accept()
        QMessageBox.information(self, "Succès", f"{len(df)} série(s) importée(s) avec succès !")
    
    def set_data(self, data) :
        row = self.table.rowCount()
        self.table.insertRow(row)
        for i, col in enumerate(self.columns) :
            value = getattr(data, col.lower(), "")
            self.table.setItem(row, i+1, QTableWidgetItem("" if value is None else str(value)))
            
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(lambda checked=False, current_data=data: self.open_edit_window(current_data))
        self.table.setCellWidget(row, 0, edit_button)
    
    def load(self):
        for data in self.data:
            self.set_data(data)
    
    def add(self, data):
        cal_data = self.calculate(data)
        self.db.add(self.table_name, cal_data)
        self.set_data(cal_data)
    
    def open_edit_window(self, data):
        values = {col: getattr(data, col.lower(), "") for col in self.columns}
        field_types = {field.name: field.type for field in fields(self.model_cls)}
        dialog = EditData(self.columns, values=values, field_types=field_types, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_values = dialog.get_casted_data()
            # Handle title change: rename image file if present
            old_title = getattr(data, 'titre', '')
            new_title = updated_values.get('Titre', old_title)
            if new_title != old_title and old_title != "":
                try:
                    base_old = sanitize_filename(old_title)
                    base_new = sanitize_filename(new_title)
                    exts = ['.jpg', '.jpeg', '.png', '.webp']
                    for ext in exts:
                        old_path = Path(self.data_folder) / (base_old + ext)
                        if old_path.exists():
                            new_path = Path(self.data_folder) / (base_new + ext)
                            # Ensure parent exists
                            Path(self.data_folder).mkdir(parents=True, exist_ok=True)
                            try:
                                old_path.rename(new_path)
                            except Exception:
                                pass
                            break
                except Exception:
                    pass

            for col in self.columns:
                setattr(data, col.lower(), updated_values.get(col, getattr(data, col.lower(), "")))
            cal_data = self.calculate(data)
            self.db.update(self.table_name, cal_data)
            self.refresh()
    
    def get_addable_columns(self):
        return [col for col in self.columns if col not in self.hidden_columns]

    def open_add_window(self) :
        addable_columns = self.get_addable_columns()
        add_window = AddData(addable_columns)
        add_window.exec_()
        new_data = add_window.get_data()
        
        if new_data["Titre"] != "" :
            data = self.model_cls()
            for col in self.columns :
                setattr(data, col.lower(), new_data.get(col, ""))
            
            self.add(data)
    
    def open_del_window(self) :
        del_window = DelData()
        del_window.exec_()
        data = del_window.get_data()
        
        self.db.delete(self.table_name, self.model_cls(id=int(data)))
        
        self.refresh()
