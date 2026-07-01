from dataclasses import fields

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, \
                            QTableWidgetItem, QPushButton, QSizePolicy, QDialog, QLabel, QMessageBox
import pandas as pd

from src.models.webtoon import Webtoon
from src.view.add_window import AddData
from src.view.del_window import DelData
from src.view.edit_window import EditData


class WebtoonWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        
        self.db = db
        self.table_name = "webtoon"
        self.model_cls = Webtoon
        self.data = self.db.get(self.table_name, self.model_cls)
        
        self.columns = ["Titre", "Auteur", "Type", "Genre",
                        "Updated", "Etat", "Note",
                        "nb_ep_vu", "nb_ep_res", "nb_ep_tot", "nb_vu"]
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns) + 1)
        self.table.setHorizontalHeaderLabels([""] + self.columns)
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
        self.data = self.db.get(self.table_name, self.model_cls)
        self.table.setRowCount(0)  # Vide le tableau
        self.load()
    
    def calculate(self, data: Webtoon):
        data.nb_ep_res = data.nb_ep_tot - data.nb_ep_vu
        
        data.etat = "FINI" if data.note != "" else "EN COURS"
        
        if data.nb_ep_tot == 0 :
            data.updated = "PAS SORTI"
        elif data.nb_ep_tot > data.nb_ep_vu :
            data.etat = "EN COURS"
        elif data.nb_ep_tot == data.nb_ep_vu :
            data.etat == "FINI"
        
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
    
    def set_data(self, data : Webtoon) :
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
    
    def add(self, data: Webtoon):
        cal_data = self.calculate(data)
        self.db.add(self.table_name, cal_data)
        self.set_data(cal_data)

    def open_edit_window(self, data):
        values = {col: getattr(data, col.lower(), "") for col in self.columns}
        field_types = {field.name: field.type for field in fields(self.model_cls)}
        dialog = EditData(self.columns, values=values, field_types=field_types, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_values = dialog.get_casted_data()
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
        
        self.db.delete(self.table_name, Webtoon(id=int(data)))
        
        self.refresh()