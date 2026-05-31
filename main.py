import sys
from PyQt5.QtWidgets import (QApplication)
from PyQt5.QtGui import QIcon

from src.view.main_window import CulturApp
from src.services.config_manager import ConfigManager

import warnings
warnings.filterwarnings("ignore")

if __name__ == "__main__":
    # Initialiser le gestionnaire de configuration
    config_manager = ConfigManager()
    data_folder = config_manager.get_data_folder()
    
    app = QApplication(sys.argv)
    window = CulturApp(data_folder=str(data_folder))
    window.setWindowIcon(QIcon("src/assets/icon.png"))
    window.showMaximized()
    window.show()
    sys.exit(app.exec_())
