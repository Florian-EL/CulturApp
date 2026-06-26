from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QLabel


class EditData(QDialog):
    def __init__(self, columns, values=None, field_types=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Data")
        self.layout = QVBoxLayout(self)

        self.columns = columns
        self.inputs = {}

        for col in self.columns:
            row_layout = QHBoxLayout()
            label = QLabel(col)
            label.setStyleSheet("font-weight: bold;")
            label.setFixedWidth(120)
            row_layout.addWidget(label)

            input_field = QLineEdit()
            input_field.setPlaceholderText(col)
            input_field.setMaxLength(255)
            input_field.setFixedHeight(28)
            if values is not None:
                input_field.setText(str(values.get(col, "")))
            self.inputs[col] = input_field
            row_layout.addWidget(input_field)

            self.layout.addLayout(row_layout)

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
            return int(value) if str(value).strip() != "" else 0
        if field_type is float:
            return float(value) if str(value).strip() != "" else 0.0
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
