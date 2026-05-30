from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class FilmWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.label_count = QLabel("0 films")
        layout.addWidget(self.label_count)

    def update_count(self, nb_films):
        self.label_count.setText(f"{nb_films} films")