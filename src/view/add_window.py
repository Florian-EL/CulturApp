from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QComboBox, QLabel, QHBoxLayout, QWidget

class AddData(QDialog) :
    def __init__(self, columns, content_type=None, field_options=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Data")
        self.main_layout = QVBoxLayout()
        
        self.columns = columns
        self.content_type = content_type
        self.field_options = field_options or {}
        
        self.inputs = {}
        
        # Create a scrollable area for fields
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        for col in self.columns:
            # Create a row with label and input
            row_layout = QHBoxLayout()
            
            label = QLabel(col)
            label.setFixedWidth(140)
            row_layout.addWidget(label)
            
            # Check if this field has dropdown options
            col_options = self.field_options.get(col, [])
            
            if col_options:
                # Use ComboBox for fields with options
                combo_box = QComboBox()
                combo_box.addItem("")  # Add empty option
                combo_box.addItems(col_options)
                self.inputs[col] = combo_box
                row_layout.addWidget(combo_box)
            else:
                # Use LineEdit for regular text fields
                input_field = QLineEdit()
                input_field.setPlaceholderText(col)
                self.inputs[col] = input_field
                row_layout.addWidget(input_field)
            
            scroll_layout.addLayout(row_layout)
        
        scroll_layout.addStretch()
        self.main_layout.addWidget(scroll_widget)

        self.add_button = QPushButton("Ajouter")
        self.add_button.clicked.connect(self.accept)
        self.main_layout.addWidget(self.add_button)
        
        self.setLayout(self.main_layout)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
    def get_data(self):
        data = {}
        
        for col in self.columns:
            widget = self.inputs.get(col)
            if isinstance(widget, QComboBox):
                data[col] = widget.currentText()
            else:
                data[col] = widget.text()
        
        return data
