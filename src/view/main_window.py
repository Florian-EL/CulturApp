from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QScrollArea, QWidget, \
    QGraphicsView, QGraphicsScene, QTableView, QTableWidget, QHeaderView, QTableWidgetItem, QSizePolicy, \
    QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor


class CulturApp(QWidget) :
    def __init__(self) :
        super().__init__()
        self.layout = QHBoxLayout()
        
        self.right_menu_layout = QHBoxLayout() #TODO -> tabwidget ou filtre
        self.stat_layout = QVBoxLayout()
        self.main_layout = QVBoxLayout()
        
        self.set_menu()
        self.set_stat()
        self.set_main()
        self.define_layout()
        
        self.setLayout(self.layout)
        
    def set_menu(self) :
        label = QLabel("Menu")
        label.setStyleSheet("background-color: red;")
        self.right_menu_layout.addWidget(label)
    
    def set_main(self) :
        label1 = QLabel("main")
        label1.setStyleSheet("background-color: green;")
        self.main_layout.addWidget(label1)
    
    def set_stat(self) :
        label2 = QLabel("stat")
        label2.setStyleSheet("background-color: blue;")
        self.stat_layout.addWidget(label2)
        
    def define_layout(self) :
        self.stat_layout.addLayout(self.main_layout)
        self.right_menu_layout.addLayout(self.stat_layout)
        
        self.layout.addLayout(self.right_menu_layout)