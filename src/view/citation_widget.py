from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.models.citation import Citation
from src.view.add_window import AddData
from src.view.edit_window import EditData
from src.view.gallery_widget import sanitize_filename


class CitationWidget(QWidget):
    def __init__(self, db, columns, data_folder, initial_sort, parent=None):
        super().__init__(parent)
        self.db = db
        self.columns = columns
        self.data_folder = Path(data_folder)
        self.parent_window = parent
        self.initial_sort_rules = initial_sort
        self.all_data = []
        self.data = []
        self.row_data = {}

        layout = QHBoxLayout(self)
        
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
                if isinstance(rule, str):
                    rule = {"field": rule, "order": "asc"}
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
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(8)
        controls_group.setFixedWidth(330)

        self.table = QTableWidget(0, len(self.columns) + 1)
        self.table.setHorizontalHeaderLabels(["Couverture"] + self.columns)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self.edit_row)
        self.table.setColumnHidden(2, True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 90)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # Shared buttons visible on both tabs
        shared_buttons = QVBoxLayout()
        add_button = QPushButton("Add")
        add_button.setStyleSheet("background-color: green;")
        add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        add_button.clicked.connect(self.add_citation)

        del_button = QPushButton("Del")
        del_button.setStyleSheet("background-color: red;")
        del_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        del_button.clicked.connect(self.delete_selected)

        shared_buttons.addWidget(add_button)
        shared_buttons.addWidget(del_button)
        main_content_layout.addLayout(shared_buttons)
        
        
        layout.addWidget(self.table)
        layout.addLayout(main_content_layout)
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)

        self.refresh()

    def _image_path(self, oeuvre):
        base = sanitize_filename(oeuvre)
        for extension in (".jpg", ".jpeg", ".png", ".webp"):
            path = self.data_folder / (base + extension)
            if path.exists():
                return path
        return None

    def _matches(self, citation):
        query = self.filter_edit.text().strip().lower()
        if not query:
            return True
        field = self.filter_field.currentData()
        values = [field] if field else [column.lower() for column in self.columns]
        return any(query in str(getattr(citation, value, "") or "").lower() for value in values)

    def refresh(self, _=None):
        self.all_data = self.db.get("citation", Citation)
        self.apply_view_options()
        self._load_table()

    def _load_table(self):
        self.row_data = {}
        self.table.setRowCount(0)
        current_oeuvre = None
        for citation in self.data:
            oeuvre = citation.oeuvre or "(Oeuvre inconnue)"
            if oeuvre != current_oeuvre:
                group_row = self.table.rowCount()
                self.table.insertRow(group_row)
                group_item = QTableWidgetItem(oeuvre)
                group_item.setData(Qt.UserRole, oeuvre)
                group_item.setFont(QFont("", 10, QFont.Bold))
                group_item.setTextAlignment(Qt.AlignCenter)
                self.table.setSpan(group_row, 1, 1, len(self.columns))
                self.table.setItem(group_row, 1, group_item)
                image_path = self._image_path(oeuvre)
                if image_path:
                    label = QLabel()
                    label.setAlignment(Qt.AlignCenter)
                    label.setPixmap(QPixmap(str(image_path)).scaled(70, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.table.setCellWidget(group_row, 0, label)
                self.table.setRowHeight(group_row, 110 if image_path else 32)
                current_oeuvre = oeuvre

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.row_data[row] = citation
            self.table.setItem(row, 0, QTableWidgetItem(""))
            for index, column in enumerate(self.columns, start=1):
                value = getattr(citation, column.lower(), "")
                item = QTableWidgetItem("" if value is None else str(value))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.table.setItem(row, index, item)
        self.table.resizeRowsToContents()
        self.table.setColumnHidden(2, True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.table.resizeRowsToContents()

    def _dialog_values(self, dialog):
        if dialog.exec_() != QDialog.Accepted:
            return None
        return dialog.get_casted_data()

    def add_citation(self):
        dialog = AddData(self.columns)
        dialog.exec_()
        values = dialog.get_data()
        citation = Citation(**{column.lower(): values.get(column, "") for column in self.columns})
        self.db.add("citation", citation)
        self.refresh()

    def edit_row(self, row, _column):
        citation = self.row_data.get(row)
        if citation is None:
            return
        values = {column: getattr(citation, column.lower(), "") for column in self.columns}
        field_types = {field.name: field.type for field in Citation.__dataclass_fields__.values()}
        dialog = EditData(self.columns, values=values, field_types=field_types, parent=self)
        if dialog.exec_() != QDialog.Accepted:
            updated = dialog.get_casted_data()
            for column in self.columns:
                setattr(citation, column.lower(), updated.get(column, ""))
        self.db.update("citation", citation)
        self.refresh()

    def delete_selected(self):
        citation = self.row_data.get(self.table.currentRow())
        if citation is None:
            return
        self.db.delete("citation", citation)
        self.refresh()

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Importer un fichier CSV", "", "CSV (*.csv)")
        if file_path:
            self.add_import(pd.read_csv(file_path, delimiter=";"))

    def add_import(self, dataframe):
        normalized = {str(column).strip().lower(): column for column in dataframe.columns}
        required = [column.lower() for column in self.columns]
        missing = [column for column in required if column not in normalized]
        if missing:
            QMessageBox.warning(self, "Erreur", f"Colonnes manquantes : {', '.join(missing)}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Importer des citations")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Importer {len(dataframe)} citation(s). Remplacer les données existantes ?"))
        buttons = QHBoxLayout()
        replace = QPushButton("Remplacer")
        replace.clicked.connect(lambda: self._import_rows(dataframe, normalized, dialog, True))
        append = QPushButton("Ajouter")
        append.clicked.connect(lambda: self._import_rows(dataframe, normalized, dialog, False))
        cancel = QPushButton("Annuler")
        cancel.clicked.connect(dialog.reject)
        for button in (replace, append, cancel):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        dialog.exec_()

    def _import_rows(self, dataframe, normalized, dialog, replace):
        self.db.ensure_citation_table()
        if replace:
            for citation in self.all_data:
                self.db.delete("citation", citation)
        for _, row in dataframe.iterrows():
            values = {}
            for column in self.columns:
                value = row[normalized[column.lower()]]
                values[column.lower()] = "" if pd.isna(value) else str(value)
            self.db.add("citation", Citation(**values))
        dialog.accept()
        self.refresh()
    
    def _get_available_fields(self):
        fields = [("Citation", "citation"), ("Oeuvre", "oeuvre"), ("Personnage", "personnage"), ("Artiste", "artiste")]
        seen = {item[1] for item in fields}
        for col in self.columns:
            value = col.lower()
            if value not in seen:
                fields.append((col, value))
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
                populated = [data for data in filtered if getattr(data, sort_field, "") not in (None, "")]
                empty = [data for data in filtered if getattr(data, sort_field, "") in (None, "")]
                filtered = sorted(
                    populated,
                    key=lambda data: self._sort_value(data, sort_field),
                    reverse=reverse,
                ) + empty

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