from dataclasses import fields

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QSizePolicy,
    QDialog,
    QLabel,
    QMessageBox,
    QTabWidget,
    QLineEdit,
    QComboBox,
    QHeaderView,
    QFrame,
    QGroupBox,
)
from PySide6.QtCore import QTimer
import pandas as pd

from src.view.add_window import AddData
from src.view.del_window import DelData
from src.view.edit_window import EditData
from src.view.gallery_widget import GalleryWidget, sanitize_filename
from pathlib import Path


class TypeWidget(QWidget):
    def __init__(self, db, table_name, model_cls, columns, hidden_columns, data_folder, initial_sort_rules=None):
        super().__init__()
        
        self.db = db
        self.table_name = table_name
        self.model_cls = model_cls
        self.columns = columns
        self.hidden_columns = hidden_columns
        self.data_folder = data_folder
        self.initial_sort_rules = initial_sort_rules or []

        layout = QHBoxLayout(self)
        layout.setSpacing(12)

        self.all_data = []
        self.data = []

        main_content_layout = QVBoxLayout()
        main_content_layout.setSpacing(8)

        controls_group = QGroupBox()
        controls_group.setStyleSheet("""
        #sidePanel {
            background: palette(base);
            border: 1px solid palette(mid);
            border-radius: 8px;
        }
        """)
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(8)
        controls_layout.setContentsMargins(8, 12, 8, 8)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        top_row_2 = QHBoxLayout()
        top_row_2.setSpacing(6)

        filter_label = QLabel()
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Rechercher...")
        self.filter_edit.setFixedWidth(140)
        self.filter_edit.textChanged.connect(self.apply_view_options)
        top_row.addWidget(filter_label)
        top_row.addWidget(self.filter_edit)

        self.filter_field_combo = QComboBox()
        self.filter_field_combo.setFixedWidth(110)
        self.filter_field_combo.addItem("Tous", None)
        for display_name, value in self._get_available_fields():
            self.filter_field_combo.addItem(display_name, value)
        self.filter_field_combo.currentIndexChanged.connect(self.apply_view_options)
        top_row.addWidget(self.filter_field_combo)

        refresh_button = QPushButton("Rafraîchir")
        refresh_button.setFixedWidth(90)
        refresh_button.clicked.connect(self.refresh)
        top_row_2.addWidget(refresh_button)

        reset_button = QPushButton("Réinitialiser")
        reset_button.setFixedWidth(100)
        reset_button.clicked.connect(self.reset_filters)
        top_row_2.addWidget(reset_button)

        controls_layout.addLayout(top_row)
        controls_layout.addLayout(top_row_2)

        sort_frame = QFrame()
        sort_frame.setFrameShape(QFrame.StyledPanel)
        sort_frame.setLineWidth(1)
        sort_panel_layout = QVBoxLayout(sort_frame)
        sort_panel_layout.setSpacing(6)

        self.sort_rows_layout = QVBoxLayout()
        self.sort_rows_layout.setSpacing(6)
        self.sort_rows = []
        if self.initial_sort_rules:
            for rule in self.initial_sort_rules:
                self._add_sort_row(
                    field_name=rule.get("field"),
                    reverse=str(rule.get("order", "asc")).lower() in {"desc", "descending", "descroissant"},
                )
        else:
            self._add_sort_row(field_name=None, reverse=False)
        sort_panel_layout.addLayout(self.sort_rows_layout)

        add_sort_button = QPushButton("+ Ajouter un tri")
        add_sort_button.clicked.connect(self._add_sort_row)
        sort_panel_layout.addWidget(add_sort_button)

        controls_layout.addWidget(sort_frame)

        main_content_layout.addWidget(controls_group)


        # Create tabs: Table and Gallery
        self.tab_widget = QTabWidget()

        # Table tab
        table_page = QWidget()
        table_layout = QVBoxLayout(table_page)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns) + 1)
        self.table.setHorizontalHeaderLabels([""] + self.columns)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        table_layout.addWidget(self.table)

        self._data_loaded = False
        self._schedule_initial_load()

        # Buttons moved to shared area below tabs
        self.gallery = GalleryWidget(self.db, self.table_name, self.model_cls, self.columns, self.data_folder, parent=self)
        self.tab_widget.addTab(self.gallery, "Gallery")
        self.tab_widget.addTab(table_page, "Table")

        # Refresh gallery when switching to that tab
        self.tab_widget.currentChanged.connect(self.on_subtab_changed)
        
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.tab_widget)
        layout.addLayout(main_content_layout)
        
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)
        

        # Shared buttons visible on both tabs
        shared_buttons = QVBoxLayout()
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
        main_content_layout.addLayout(shared_buttons)
    
    def showEvent(self, event):
        """Appelé quand le widget devient visible"""
        super().showEvent(event)
        if not self._data_loaded:
            self._schedule_initial_load()
        
    def _get_available_fields(self):
        fields = [("Titre", "titre"), ("État", "etat"), ("Note", "note")]
        seen = {item[1] for item in fields}
        for col in self.columns:
            value = col.lower()
            if value not in seen:
                fields.append((col, value))
                seen.add(value)

        extra_fields = [("Auteur", "auteur"), ("Nom série", "nom_serie"), ("Nb ép. tot", "nb_ep_tot"), ("Nb ép. vu", "nb_ep_vu"), ("Nb ép. res", "nb_ep_res")]
        for display_name, value in extra_fields:
            if value not in seen:
                fields.append((display_name, value))
                seen.add(value)
        return fields

    def _get_sortable_fields(self):
        return self._get_available_fields()

    def _add_sort_row(self, field_name=None, reverse=False):
        row_widget = QFrame()
        row_widget.setFrameShape(QFrame.StyledPanel)
        row_widget.setStyleSheet("QFrame { border: 1px solid #999; border-radius: 6px; }")
        row_layout_final = QHBoxLayout(row_widget)
        row_layout = QVBoxLayout()

        field_combo = QComboBox()
        field_combo.addItem("Aucun", None)
        for display_name, value in self._get_sortable_fields():
            field_combo.addItem(display_name, value)
        if field_name is not None:
            index = field_combo.findData(field_name)
            if index >= 0:
                field_combo.setCurrentIndex(index)
        field_combo.currentIndexChanged.connect(self.apply_view_options)
        row_layout.addWidget(field_combo)

        order_combo = QComboBox()
        order_combo.addItems(["Croissant", "Décroissant"])
        if reverse:
            order_combo.setCurrentIndex(1)
        order_combo.currentIndexChanged.connect(self.apply_view_options)
        row_layout.addWidget(order_combo)

        remove_button = QPushButton("×")
        remove_button.setFixedWidth(24)
        remove_button.setToolTip("Supprimer ce tri")
        remove_button.clicked.connect(lambda _, widget=row_widget, combo_pair=(field_combo, order_combo): self._remove_sort_row(widget, combo_pair))
        
        row_layout_final.addLayout(row_layout)
        row_layout_final.addWidget(remove_button)

        self.sort_rows_layout.addWidget(row_widget)
        self.sort_rows.append((field_combo, order_combo))

    def _remove_sort_row(self, widget, combo_pair):
        field_combo, order_combo = combo_pair
        if (field_combo, order_combo) in self.sort_rows:
            self.sort_rows.remove((field_combo, order_combo))
        widget.setParent(None)
        widget.deleteLater()
        self.apply_view_options()

    def _normalize_search_value(self, value):
        if value is None:
            return ""
        return str(value).strip().lower()

    def _matches_filter(self, data, field_name, query):
        if not query:
            return True

        if field_name is None:
            values = []
            for attr in ["titre", "auteur", "nom_serie", "note", "etat", "nb_ep_tot", "nb_ep_vu", "nb_ep_res"]:
                values.append(self._normalize_search_value(getattr(data, attr, "")))
            for col in self.columns:
                values.append(self._normalize_search_value(getattr(data, col.lower(), "")))
            return any(query in value for value in values if value)

        value = self._normalize_search_value(getattr(data, field_name, ""))
        return query in value

    def _sort_value(self, data, field_name):
        if not field_name:
            return ""

        value = getattr(data, field_name, "")
        if value in (None, ""):
            return (1, "")

        if field_name in {"nb_ep_tot", "nb_ep_vu", "nb_ep_res", "note", "nb_vu", "nb_saison", "ep_act", "ep_deb", "priorite", "sortie", "annee_vu", "type", "vo", "cinema"}:
            try:
                return (0, float(value))
            except (TypeError, ValueError):
                return (0, 0)

        if field_name == "etat":
            order = {"FINI": 2, "EN COURS": 1}
            return (0, order.get(str(value).upper(), 0))

        return (0, self._normalize_search_value(value))

    def apply_view_options(self, _=None):
        query = self.filter_edit.text().strip().lower()
        field_name = self.filter_field_combo.currentData()

        filtered = list(self.all_data)
        if query:
            filtered = [data for data in filtered if self._matches_filter(data, field_name, query)]

        sort_rules = []
        for field_combo, order_combo in self.sort_rows:
            sort_field = field_combo.currentData()
            if sort_field:
                sort_rules.append((sort_field, order_combo.currentIndex() == 1))

        if sort_rules:
            for sort_field, reverse in reversed(sort_rules):
                filtered = sorted(filtered, key=lambda data: self._sort_value(data, sort_field), reverse=reverse)

        self.data = filtered
        return filtered

    def reset_filters(self):
        self.filter_edit.clear()
        self.filter_field_combo.setCurrentIndex(0)

        for row_index, (field_combo, order_combo) in enumerate(self.sort_rows):
            field_combo.setCurrentIndex(0)
            order_combo.setCurrentIndex(0)

        self.apply_view_options()
        self.refresh()

    def _schedule_initial_load(self):
        if self._data_loaded:
            return
        QTimer.singleShot(0, self._load_initial_data)

    def _load_initial_data(self):
        if self._data_loaded:
            return
        self.refresh()
        self._data_loaded = True

    def _load_data(self):
        self.all_data = [self.calculate(data) for data in self.db.get(self.table_name, self.model_cls)]
        self.data = self.apply_view_options(self.all_data)

    def refresh(self):
        """Rafraîchit les données depuis la base de données"""
        self._load_data()
        self.table.setRowCount(0)
        self.load()
        # Refresh gallery view as well
        try:
            if hasattr(self, 'gallery'):
                self.gallery.refresh(self.data)
        except Exception:
            pass

    def on_subtab_changed(self, index):
        # If switching to gallery tab, refresh its content
        try:
            if self.tab_widget.tabText(index) == "Gallery":
                self.gallery.refresh(self.data)
        except Exception:
            pass
    
    def calculate(self, data):
        if self.table_name == "manga" :
            data.nb_ep_vu = data.ep_act
        
        data.nb_ep_res = int(data.nb_ep_tot) - int(data.nb_ep_vu)
        data.etat = "FINI" if int(data.nb_ep_res) == 0 else "EN COURS"

        if self.table_name == "serie" :
            nb_saison = 0
            data.nb_ep_tot = 0
            data.nb_ep_vu = 0
            for col in self.columns:
                if col.endswith("_tot") and col.lower() != "nb_ep_tot":
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
            data.etat = "FINI"
        
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
    
    def set_data(self, data, row):
        for i, col in enumerate(self.columns):
            value = getattr(data, col.lower(), "")
            self.table.setItem(row, i + 1, QTableWidgetItem("" if value is None else str(value)))

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(lambda checked=False, current_data=data: self.open_edit_window(current_data))
        self.table.setCellWidget(row, 0, edit_button)

    def load(self):
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(self.data))
        for row, data in enumerate(self.data):
            self.set_data(data, row)
        self.table.resizeRowsToContents()
        self.table.setUpdatesEnabled(True)
    
    def add(self, data):
        cal_data = self.calculate(data)
        self.db.add(self.table_name, cal_data)
        self.refresh()
    
    def open_edit_window(self, data):
        values = {col: getattr(data, col.lower(), "") for col in self.columns}
        field_types = {field.name: field.type for field in fields(self.model_cls)}
        dialog = EditData(self.get_addable_columns(), values=values, field_types=field_types, parent=self)
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
                setattr(data, col.lower(), new_data.get(col, 0))
            
            self.add(data)
    
    def open_del_window(self) :
        del_window = DelData()
        del_window.exec_()
        data = del_window.get_data()
        
        self.db.delete(self.table_name, self.model_cls(id=int(data)))
        
        self.refresh()
