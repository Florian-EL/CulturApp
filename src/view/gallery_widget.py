import os
from pathlib import Path
from urllib.request import urlretrieve

from dataclasses import fields

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QDialog,
    QInputDialog,
    QScrollArea,
)


def sanitize_filename(name: str) -> str:
    invalid = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for ch in invalid:
        name = name.replace(ch, '_')
    return name.strip()


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class GalleryWidget(QWidget):

    CARD_WIDTH = 180
    IMAGE_WIDTH = 160
    IMAGE_HEIGHT = 240

    def __init__(
        self,
        db,
        table_name,
        model_cls,
        columns,
        data_folder: Path,
        parent=None,
    ):
        super().__init__(parent)

        self.db = db
        self.table_name = table_name
        self.model_cls = model_cls
        self.columns = columns
        self.data_folder = Path(data_folder) if data_folder else Path(".")

        main_layout = QVBoxLayout(self)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)

        main_layout.addWidget(self.scroll)

        self.container = QWidget()
        self.grid = QGridLayout(self.container)

        self.grid.setSpacing(18)
        self.grid.setContentsMargins(20, 20, 20, 20)

        self.scroll.setWidget(self.container)

        bottom = QHBoxLayout()

        self.refresh_btn = QPushButton("⟳ Refresh")
        self.refresh_btn.clicked.connect(self.refresh)

        bottom.addWidget(self.refresh_btn)
        bottom.addStretch()

        main_layout.addLayout(bottom)

        self.refresh()

    # ------------------------------------------------------------------
    # Image helpers
    # ------------------------------------------------------------------

    def find_image(self, title: str):

        base = sanitize_filename(title)

        for ext in (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        ):

            candidate = self.data_folder / (base + ext)

            if candidate.exists():
                return str(candidate)

        return None

    def download_image_for(self, title: str, url: str):

        try:

            base = sanitize_filename(title)

            _, ext = os.path.splitext(url)

            if ext.lower() not in (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            ):
                ext = ".jpg"

            self.data_folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            target = self.data_folder / (base + ext)

            urlretrieve(url, str(target))

            return str(target)

        except Exception:
            return None

    def request_and_download(self, data):

        url, ok = QInputDialog.getText(
            self,
            "Nouvelle image",
            "URL de l'image :",
        )

        if not (ok and url):
            return

        result = self.download_image_for(
            getattr(data, "titre", ""),
            url,
        )

        if result:
            self.refresh()

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    def get_author(self, data):

        if hasattr(data, "auteur"):
            return getattr(data, "auteur")

        if hasattr(data, "nom_serie"):
            return getattr(data, "nom_serie")

        return ""

    def format_note(self, value):

        if value in (None, ""):
            return ""

        try:
            note = float(value)
        except Exception:
            return str(value)

        stars = round(note / 4)

        stars = max(0, min(5, stars))

        return "{}{}   {:.1f}/10".format(
            "★" * stars,
            "☆" * (5 - stars),
            note/2,
        )

    def clear_grid(self):

        while self.grid.count():

            item = self.grid.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def compute_columns(self):

        viewport_width = self.scroll.viewport().width()

        spacing = self.grid.spacing()

        cols = max(
            1,
            viewport_width // (self.CARD_WIDTH + spacing),
        )

        return cols

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self):

        self.clear_grid()

        try:
            datas = self.db.get(
                self.table_name,
                self.model_cls,
            )
        except Exception:
            datas = []

        cols = self.compute_columns()

        for index, data in enumerate(datas):

            row = index // cols
            column = index % cols

            card = self.make_card(data)

            self.grid.addWidget(
                card,
                row,
                column,
            )

        self.grid.setRowStretch(
            len(datas) // cols + 1,
            1,
        )

    def resizeEvent(self, event):

        super().resizeEvent(event)

        self.refresh()

    def make_card(self, data):

        title = getattr(data, "titre", "")
        author = self.get_author(data)
        note = getattr(data, "note", "")

        card = QWidget()
        card.setFixedWidth(self.CARD_WIDTH)

        card.setStyleSheet("""
        QWidget{
            background:#2b2b2b;
            border-radius:12px;
        }

        QWidget:hover{
            background:#3a3a3a;
        }

        QLabel{
            color:white;
            background:transparent;
        }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(6)

        image = ClickableLabel()
        image.setAlignment(Qt.AlignCenter)
        image.setCursor(Qt.PointingHandCursor)
        image.setFixedSize(
            self.IMAGE_WIDTH,
            self.IMAGE_HEIGHT
        )

        image_path = self.find_image(title)

        if image_path:

            pix = QPixmap(image_path)

            if not pix.isNull():
                image.setPixmap(
                    pix.scaled(
                        image.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
            else:
                image.setText("Image")

        else:

            image.setText("No Image")

        image.clicked.connect(
            lambda d=data: self.show_details(d)
        )

        layout.addWidget(
            image,
            alignment=Qt.AlignCenter
        )

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)

        f = title_label.font()
        f.setBold(True)
        f.setPointSize(f.pointSize()+1)
        title_label.setFont(f)

        layout.addWidget(title_label)

        author_label = QLabel(author)
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setWordWrap(True)
        author_label.setStyleSheet("""
        color:#bbbbbb;
        """)
        layout.addWidget(author_label)

        rating = QLabel(self.format_note(note))
        rating.setAlignment(Qt.AlignCenter)
        rating.setStyleSheet("""
        color:#f7d154;
        font-weight:bold;
        """)
        layout.addWidget(rating)

        layout.addStretch()

        return card


    def show_details(self, data):

        dialog = QDialog(self)
        dialog.setWindowTitle(
            getattr(data, "titre", "Détails")
        )

        dialog.resize(700,650)

        dialog.setStyleSheet("""
        QDialog{
            background:#252525;
        }

        QLabel{
            color:white;
            font-size:12px;
        }

        QPushButton{
            padding:8px;
        }
        """)

        layout = QVBoxLayout(dialog)

        title = getattr(data,"titre","")

        image_path = self.find_image(title)

        if image_path:

            pix = QPixmap(image_path)

            if not pix.isNull():

                img = QLabel()

                img.setAlignment(Qt.AlignCenter)

                img.setPixmap(
                    pix.scaledToWidth(
                        320,
                        Qt.SmoothTransformation
                    )
                )

                layout.addWidget(img)

        title_lbl = QLabel(title)

        font = title_lbl.font()
        font.setPointSize(font.pointSize()+5)
        font.setBold(True)

        title_lbl.setFont(font)
        title_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_lbl)

        author = self.get_author(data)

        if author:

            lbl = QLabel(author)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("""
            color:#bbbbbb;
            """)
            layout.addWidget(lbl)

        note = getattr(data,"note","")

        if note != "":

            lbl = QLabel(self.format_note(note))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("""
            color:#f7d154;
            font-size:15px;
            """)
            layout.addWidget(lbl)

        layout.addSpacing(15)

        for field in fields(self.model_cls):

            value = getattr(
                data,
                field.name,
                ""
            )

            row = QLabel(
                f"<b>{field.name}</b><br>{value}"
            )

            row.setWordWrap(True)

            layout.addWidget(row)

        layout.addStretch()

        buttons = QHBoxLayout()

        image_btn = QPushButton("Changer l'image")

        image_btn.clicked.connect(
            lambda _, d=data: self.request_and_download(d)
        )

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)

        buttons.addStretch()
        buttons.addWidget(image_btn)
        buttons.addWidget(close_btn)

        layout.addLayout(buttons)

        dialog.exec_()

