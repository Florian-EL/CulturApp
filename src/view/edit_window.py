from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QLabel, QWidget, QGridLayout, QScrollArea, QComboBox


class EditData(QDialog):
    def __init__(self, columns, values=None, field_types=None, content_type=None, field_options=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Data")
        self.layout = QVBoxLayout(self)

        self.columns = columns
        self.inputs = {}
        self.content_type = content_type
        self.field_options = field_options or {}

        field_count = len(self.columns)
        max_rows = 10
        column_count = min(3, max(1, (field_count + max_rows - 1) // max_rows))
        rows_per_column = (field_count + column_count - 1) // column_count

        content_widget = QWidget()
        grid_layout = QGridLayout(content_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(8)

        for index, col in enumerate(self.columns):
            col_index = index // rows_per_column
            row_index = index % rows_per_column

            label = QLabel(col)
            label.setStyleSheet("font-weight: bold;")
            label.setFixedWidth(140)

            # Check if this field has dropdown options
            col_options = self.field_options.get(col, [])
            
            if col_options:
                # Use ComboBox for fields with options
                input_field = QComboBox()
                input_field.addItem("")  # Add empty option
                input_field.addItems(col_options)
                
                # Set current value if provided
                if values is not None:
                    current_value = str(values.get(col, ""))
                    index = input_field.findText(current_value)
                    if index >= 0:
                        input_field.setCurrentIndex(index)
                
                input_field.setFixedWidth(128)
            else:
                # Use LineEdit for regular text fields
                input_field = QLineEdit()
                input_field.setPlaceholderText(col)
                input_field.setMaxLength(512)
                input_field.setFixedWidth(128)
                input_field.setFixedHeight(28)
                if values is not None:
                    input_field.setText(str(values.get(col, "")))
            
            self.inputs[col] = input_field

            grid_layout.addWidget(label, row_index, col_index * 2)
            grid_layout.addWidget(input_field, row_index, col_index * 2 + 1)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        scroll_area.setHorizontalScrollBarPolicy(scroll_area.horizontalScrollBarPolicy())
        scroll_area.setVerticalScrollBarPolicy(scroll_area.verticalScrollBarPolicy())

        self.setMinimumWidth(1024)
        self.setMinimumHeight(256)
        # self.setMaximumWidth(1040)
        # self.setMaximumHeight(720)

        self.layout.addWidget(scroll_area)

        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Enregistrer")
        save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(save_button)

        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        self.layout.addLayout(buttons_layout)

        self.field_types = field_types or {}

    def get_data(self):
        data = {}
        for col in self.columns:
            widget = self.inputs.get(col)
            if isinstance(widget, QComboBox):
                data[col] = widget.currentText()
            else:
                data[col] = widget.text()
        return data

    def get_casted_data(self):
        raw_data = self.get_data()
        casted_data = {}
        for col, value in raw_data.items():
            field_type = self.field_types.get(col.lower(), str)
            casted_data[col] = self._cast_value(value, field_type)
        return casted_data

    @staticmethod
    def _cast_value(value, field_type):
        if value is None:
            return ""
        if field_type is str:
            return str(value)
        if field_type is int:
            return int(value) if str(value).strip() != "" else ""
        if field_type is float:
            return float(value) if str(value).strip() != "" else ""
        if field_type is bool:
            if isinstance(value, bool):
                return value
            text = str(value).strip().lower()
            if text in {"1", "true", "yes", "y", "oui", "o"}:
                return True
            if text in {"0", "false", "no", "n", "non", "non"}:
                return False
            return bool(text)
        return value
