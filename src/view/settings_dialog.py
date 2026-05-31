from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from src.services.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """Dialogue pour configurer les paramètres de l'application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Paramètres")
        self.setGeometry(100, 100, 600, 200)
        
        layout = QVBoxLayout()
        
        # Section dossier data
        data_folder_layout = QHBoxLayout()
        data_folder_label = QLabel("Dossier Data :")
        self.data_folder_input = QLineEdit()
        self.data_folder_input.setText(str(self.config_manager.get_data_folder()))
        self.data_folder_input.setReadOnly(True)
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.browse_data_folder)
        
        data_folder_layout.addWidget(data_folder_label)
        data_folder_layout.addWidget(self.data_folder_input)
        data_folder_layout.addWidget(browse_button)
        
        # Boutons de contrôle
        button_layout = QHBoxLayout()
        save_button = QPushButton("Enregistrer")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # Ajouter les sections au layout principal
        layout.addLayout(data_folder_layout)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_data_folder(self):
        """Ouvre un dialogue pour sélectionner le dossier data"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier data",
            str(self.config_manager.get_data_folder())
        )
        if folder:
            self.data_folder_input.setText(folder)
    
    def save_settings(self):
        """Enregistre les paramètres"""
        data_folder = self.data_folder_input.text().strip()
        
        if not data_folder:
            QMessageBox.warning(self, "Erreur", "Veuillez spécifier un dossier data")
            return
        
        try:
            self.config_manager.set_data_folder(data_folder)
            QMessageBox.information(
                self,
                "Succès",
                "Les paramètres ont été enregistrés.\n"
                "Redémarrez l'application pour appliquer les changements."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
