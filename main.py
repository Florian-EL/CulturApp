import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from src.view.main_window import CulturApp

import warnings
warnings.filterwarnings("ignore")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CulturApp(False)
    window.setWindowIcon(QIcon("src/assets/icon.png"))
    window.showMaximized()
    window.show()
    sys.exit(app.exec_())
