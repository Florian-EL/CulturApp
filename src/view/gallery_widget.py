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
    QFrame,
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
        cols = max(1, viewport_width // (self.CARD_WIDTH + spacing),)
        return cols

    def refresh(self):
        self.clear_grid()
        try:
            datas = self.db.get(self.table_name, self.model_cls)
        except Exception:
            datas = []

        cols = self.compute_columns()
        for index, data in enumerate(datas):
            row = index // cols
            column = index % cols

            card = self.make_card(data)
            self.grid.addWidget(card, row, column)

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

        total_seen = getattr(data, "nb_ep_vu", None)
        total_count = getattr(data, "nb_ep_tot", None)

        if total_seen not in (None, "") or total_count not in (None, ""):
            seen_text = "0" if total_seen in (None, "") else str(total_seen)
            count_text = "?" if total_count in (None, "") else str(total_count)
        
        progress_label = QLabel(f"{seen_text}/{count_text}")
        progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(progress_label)

        layout.addStretch()

        return card

    def make_chip(self, text, bg_color="#2f4f7f", text_color="#e9f2ff"):
        label = QLabel(
            f"<span style='background-color:{bg_color}; color:{text_color}; padding:6px 10px; border-radius:999px; font-weight:600;'>{text}</span>"
        )
        label.setTextFormat(Qt.RichText)
        # label.setAlignment(Qt.AlignCenter)
        return label

    def make_detail_value(self, value, kind="text"):
        if kind == "chip":
            return self.make_chip(str(value))

        label = QLabel(str(value))
        label.setStyleSheet("color:white; font-size:13px;")
        label.setWordWrap(True)
        return label

    def build_detail_card(self, title, rows):
        card = QFrame()
        card.setObjectName("detailCard")
        card.setStyleSheet("""
        QFrame#detailCard{
            background:#2b2b2b;
            border:1px solid #3f3f3f;
            border-radius:16px;
        }
        QLabel{
            color:white;
            background:transparent;
        }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size:14px; font-weight:bold; color:#f7f7f7;")
        layout.addWidget(title_lbl)

        for label_text, value, kind in rows:
            row = QWidget()
            row.setStyleSheet("background:transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            label = QLabel(label_text)
            label.setStyleSheet("color:#8d95a7; font-size:11px; font-weight:600; text-transform:uppercase;")
            label.setWordWrap(True)
            row_layout.addWidget(label)

            value_widget = self.make_detail_value(value)
            row_layout.addStretch()
            row_layout.addWidget(value_widget, stretch=1)
            layout.addWidget(row)

        return card

    def get_country_value(self, data):
        value = getattr(data, "vo", "")
        if value not in (None, ""):
            return str(value)
        return ""

    def get_progression_rows(self, data):
        season_rows = []
        for season_num in range(1, 9):
            vu = getattr(data, f"s{season_num}_vu", None)
            total = getattr(data, f"s{season_num}_tot", None)

            if vu not in (None, "") or total not in (None, ""):
                vu_text = "0" if vu in (None, "") else str(vu)
                total_text = "?" if total in (None, "") else str(total)
                season_rows.append((f"Saison {season_num}", f"{vu_text}/{total_text}", "text"))

        if season_rows:
            return season_rows

        total_seen = getattr(data, "nb_ep_vu", None)
        total_count = getattr(data, "nb_ep_tot", None)

        if total_seen not in (None, "") or total_count not in (None, ""):
            seen_text = "0" if total_seen in (None, "") else str(total_seen)
            count_text = "?" if total_count in (None, "") else str(total_count)
            return [("", f"{seen_text}/{count_text}", "text")]

        return [("Progression", "—", "text")]

    def show_details(self, data):
        dialog = QDialog(self)
        dialog.setWindowTitle(getattr(data, "titre", "Détails"))
        dialog.resize(920, 720)
        dialog.setStyleSheet("""
        QDialog{
            background:#1f1f1f;
        }
        QLabel{
            color:white;
            font-size:12px;
        }
        QPushButton{
            padding:8px;
        }
        """)

        outer_layout = QVBoxLayout(dialog)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background:transparent;")
        outer_layout.addWidget(scroll)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(16)

        title = getattr(data, "titre", "")
        image_path = self.find_image(title)

        header = QFrame()
        header.setObjectName("detailHeader")
        header.setStyleSheet("""
        QFrame#detailHeader{
            background:qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2f3f5f, stop:1 #1e2a3d);
            border-radius:18px;
        }
        QLabel{
            color:white;
            background:transparent;
        }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(18, 18, 18, 18)
        header_layout.setSpacing(10)

        if image_path:
            pix = QPixmap(image_path)
            if not pix.isNull():
                img = QLabel()
                img.setAlignment(Qt.AlignCenter)
                img.setPixmap(pix.scaledToWidth(320, Qt.SmoothTransformation))
                header_layout.addWidget(img, alignment=Qt.AlignCenter)

        title_lbl = QLabel(title)
        font = title_lbl.font()
        font.setPointSize(font.pointSize() + 4)
        font.setBold(True)
        title_lbl.setFont(font)
        title_lbl.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_lbl)

        author = self.get_author(data)
        if author:
            author_lbl = QLabel(author)
            author_lbl.setAlignment(Qt.AlignCenter)
            author_lbl.setStyleSheet("color:#c7d6f5; font-size:13px;")
            header_layout.addWidget(author_lbl)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)
        badge_row.addStretch()

        updated_value = getattr(data, "updated", "")
        if updated_value:
            badge_row.addWidget(self.make_chip(f"Update : {updated_value}", bg_color="#5b3f94", text_color="#efe3ff"))

        state_value = getattr(data, "etat", "")
        if state_value:
            badge_row.addWidget(self.make_chip(f"Etat : {state_value}", bg_color="#8a5a00", text_color="#ffe8b3"))

        badge_row.addStretch()
        header_layout.addLayout(badge_row)

        note = getattr(data, "note", "")
        if note != "":
            note_lbl = QLabel(self.format_note(note))
            note_lbl.setAlignment(Qt.AlignCenter)
            note_lbl.setStyleSheet("color:#f7d154; font-size:15px; font-weight:bold;")
            header_layout.addWidget(note_lbl)
        else:
            note_lbl = QLabel("Pas encore notée")
            note_lbl.setAlignment(Qt.AlignCenter)
            note_lbl.setStyleSheet("color:#f7d154; font-size:15px; font-weight:bold;")
            header_layout.addWidget(note_lbl)

        content_layout.addWidget(header)

        sections_grid = QGridLayout()
        sections_grid.setSpacing(14)

        country_value = self.get_country_value(data)

        general_rows = [
            ("Auteur", author or "—", "text"),
            ("Pays", country_value or "—", "chip"),
            ("Sortie", getattr(data, "sortie", "") or "—", "text"),
        ]

        if hasattr(data, "nb_saison") and getattr(data, "nb_saison", 0):
            general_rows.append(("Saisons", str(getattr(data, "nb_saison", 0)), "text"))

        sections_grid.addWidget(
            self.build_detail_card("Œuvre", general_rows),
            0,
            0,
        )

        type_rows = [
            ("Type", getattr(data, "type", "") or "—", "text"),
            ("Genre", getattr(data, "genre", "") or "—", "text"),
        ]

        if getattr(data, "cinema", ""):
            type_rows.append(("Cinéma", getattr(data, "cinema", ""), "text"))

        sections_grid.addWidget(
            self.build_detail_card("Type & style", type_rows),
            0,
            1,
        )

        status_rows = []
        if getattr(data, "etat", ""):
            status_rows.append(("État", getattr(data, "etat", ""), "chip"))
        if getattr(data, "updated", ""):
            status_rows.append(("Mise à jour", getattr(data, "updated", ""), "chip"))
        if hasattr(data, "nb_vu") and getattr(data, "nb_vu", 0):
            status_rows.append(("Nombre vu", str(getattr(data, "nb_vu", 0)), "text"))

        sections_grid.addWidget(
            self.build_detail_card("État & suivi", status_rows or [("État", "—", "text")]),
            1,
            0,
        )

        sections_grid.addWidget(
            self.build_detail_card("Progression", self.get_progression_rows(data)),
            1,
            1,
        )

        content_layout.addLayout(sections_grid)

        content_layout.addStretch()

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
        content_layout.addLayout(buttons)

        scroll.setWidget(content)
        dialog.exec_()

