import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.models.citation import Citation
from src.models.film import Film
from src.models.manga import Manga
from src.models.roman import Roman
from src.models.serie import Serie
from src.models.wattpad import Wattpad
from src.models.webtoon import Webtoon
from src.view.gallery_widget import image_filename, sanitize_filename

MODEL_CLASSES = {
    "film": Film,
    "serie": Serie,
    "roman": Roman,
    "manga": Manga,
    "webtoon": Webtoon,
    "wattpad": Wattpad,
}

def load_type_config() -> List[tuple]:
    return [
        ("Films", "film", Film, 120),
        ("Séries", "serie", Serie, 25),
        ("Romans", "roman", Roman, 15),
        ("Mangas", "manga", Manga, 10),
        ("Webtoons", "webtoon", Webtoon, 3),
        ("Wattpads", "wattpad", Wattpad, 12),
    ]


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _format_duration(minutes: int) -> str:
    hours, remainder = divmod(max(0, int(minutes)), 60)
    return f"{hours}h{remainder:02d}"


def _get_work_key(item: Any, label: str) -> str:
    value = getattr(item, "titre_principal", None)

    return str(value).strip().lower()


def compute_type_stats(label: str, items: List[Any], avg_minutes_per_ep: int) -> Dict[str, Any]:
    count = len(items)
    e_vu = sum(_safe_int(getattr(item, "nb_ep_vu", 0)) for item in items)
    e_res = sum(_safe_int(getattr(item, "nb_ep_res", 0)) for item in items)
    e_tot = sum(_safe_int(getattr(item, "nb_ep_tot", 0)) for item in items)
    if e_tot <= 0:
        e_tot = e_vu + e_res
    if e_tot <= 0:
        e_tot = max(count, 1)

    work_keys = []
    for item in items:
        work_key = _get_work_key(item, label)
        if work_key and _safe_int(getattr(item, "nb_ep_tot", 0)) != 0:
            work_keys.append(work_key)

    unique_work_keys = set(work_keys)
    works_total = len(unique_work_keys) or max(count, 1)

    work_stats = defaultdict(lambda: {
        "ep_vu": 0,
        "ep_res": 0,
    })

    for item in items:
        work_key = _get_work_key(item, label)

        if work_key not in unique_work_keys:
            continue

        work_stats[work_key]["ep_vu"] += _safe_int(
            getattr(item, "nb_ep_vu", 0)
        )
        work_stats[work_key]["ep_res"] += _safe_int(
            getattr(item, "nb_ep_res", 0)
        )

    # Une œuvre est vue lorsque tous ses épisodes sont vus
    seen_work_keys = {
        work_key
        for work_key, stats in work_stats.items()
        if stats["ep_vu"] > 0
        and stats["ep_res"] == 0
    }

    works_seen = len(seen_work_keys)

    works_remaining = max(0, works_total - works_seen)
    percent_e = round(100 * e_vu / e_tot, 1) if e_tot else 0.0
    percent_o = round(100 * works_seen / works_total, 1) if works_total else 0.0

    notes = [_safe_float(getattr(item, "note", 0)) for item in items if _safe_float(getattr(item, "note", 0)) > 0]
    average_note = round(sum(notes) / len(notes), 2) if notes else 0.0
    std_dev = round(statistics.pstdev(notes), 2) if len(notes) > 1 else 0.0
    min_note = round(min(notes), 2) if notes else 0.0
    max_note = round(max(notes), 2) if notes else 0.0

    return {
        "type": label,
        "Épisodes\nvus": e_vu,
        "Épisodes\nrestants": e_res,
        "Épisodes\ntotaux": e_tot,
        "%\nEpisodes": f"{percent_e:.1f}%",
        "Œuvres\nvues": works_seen,
        "Œuvres\nrestantes": works_remaining,
        "Œuvres\ntotales": works_total,
        "%\nOeuvres": f"{percent_o:.1f}%",
        "Note\nmoy": f"{average_note:.2f}",
        "Écart-\ntype": f"{std_dev:.2f}",
        "Note\nmin": f"{min_note:.2f}",
        "Note\nmax": f"{max_note:.2f}",
        "1 Épisode\n%": round(1/e_tot*100, 3) if e_tot else 0.0,
        "1 Oeuvre\n%": round(1/works_total*100, 3) if works_total else 0.0,
        "Durée /\népisode\n(min)": avg_minutes_per_ep,
        "Temps\nvu": _format_duration(e_vu * avg_minutes_per_ep),
        "Temps\nrestant": _format_duration(e_res * avg_minutes_per_ep),
        "Temps\ntotal": _format_duration(e_tot * avg_minutes_per_ep),
        "percent_e": percent_e,
        "percent_o": percent_o,
        "time_minutes": e_vu * avg_minutes_per_ep,
    }

class MultiLineHeader(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setDefaultAlignment(Qt.AlignCenter)
        self.setSectionResizeMode(QHeaderView.Stretch)

    def sectionSizeFromContents(self, logicalIndex):
        size = super().sectionSizeFromContents(logicalIndex)

        text = self.model().headerData(
            logicalIndex,
            self.orientation(),
            Qt.DisplayRole
        )

        fm = self.fontMetrics()

        rect = fm.boundingRect(
            QRect(0, 0, self.sectionSize(logicalIndex), 1000),
            Qt.TextWordWrap | Qt.AlignCenter,
            str(text)
        )

        size.setHeight(rect.height() + 12)
        return size

class ProgressCard(QFrame):
    def __init__(self, title: str, percent_e: float, percent_o: float):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setStyleSheet("""
        QFrame {
            background-color: #2d2d30;
            border-radius: 10px;
            border: 1px solid #3f3f46;
        }

        QLabel#title {
            color: white;
            font-size: 12pt;
            font-weight: bold;
        }

        QLabel#label {
            color: #d0d0d0;
            font-size: 9pt;
        }

        QLabel#value {
            color: white;
            font-size: 9pt;
            font-weight: bold;
        }

        QProgressBar {
            border: none;
            border-radius: 8px;
            background: #404040;
            text-align: center;
            color: transparent;
            min-height: 16px;
            max-height: 16px;
        }

        QProgressBar::chunk {
            border-radius: 8px;
        }

        QProgressBar#episodes::chunk {
            background: #43a047;
        }

        QProgressBar#works::chunk {
            background: #2196f3;
        }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("title")
        main_layout.addWidget(title_label)

        # Episodes
        row = QHBoxLayout()
        row.setSpacing(8)

        label = QLabel("Épisodes")
        label.setObjectName("label")
        label.setFixedWidth(70)

        self.e_bar = QProgressBar()
        self.e_bar.setObjectName("episodes")
        self.e_bar.setRange(0, 100)
        self.e_bar.setValue(int(percent_e))

        value = QLabel(f"{round(percent_e, 2)} %")
        value.setObjectName("value")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value.setFixedWidth(45)

        row.addWidget(label)
        row.addWidget(self.e_bar, 1)
        row.addWidget(value)

        main_layout.addLayout(row)

        # Œuvres
        row = QHBoxLayout()
        row.setSpacing(8)

        label = QLabel("Œuvres")
        label.setObjectName("label")
        label.setFixedWidth(70)

        self.o_bar = QProgressBar()
        self.o_bar.setObjectName("works")
        self.o_bar.setRange(0, 100)
        self.o_bar.setValue(int(percent_o))

        value = QLabel(f"{round(percent_o, 2)} %")
        value.setObjectName("value")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value.setFixedWidth(45)

        row.addWidget(label)
        row.addWidget(self.o_bar, 1)
        row.addWidget(value)

        main_layout.addLayout(row)

class PieChartWidget(QWidget):
    def __init__(self, values: List[int], colors: List[str]):
        super().__init__()
        self.values = values
        self.colors = colors
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.values or all(value <= 0 for value in self.values):
            return

        rect = self.rect().adjusted(12, 12, -12, -12)
        total = sum(max(1, value) for value in self.values)
        start_angle = 90 * 16

        for value, color in zip(self.values, self.colors):
            if value <= 0:
                continue
            span = int(360 * value / total) * 16
            if span <= 0:
                span = 16
            painter.setBrush(QColor(color))
            painter.drawPie(rect, start_angle, span)
            start_angle += span

        painter.setPen(QColor("#333333"))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)


class HomeWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.data_folder = Path(db.db_folder)
        self.setLayout(QVBoxLayout())
        self.refresh()

    def _find_citation_work(self, oeuvre, items_by_type):
        normalized_oeuvre = str(oeuvre or "").strip().casefold()
        if not normalized_oeuvre:
            return None

        for _, table_name, _, _ in load_type_config():
            for item in items_by_type[table_name]:
                titles = (
                    getattr(item, "titre", ""),
                    getattr(item, "titre_principal", ""),
                    getattr(item, "titre_secondaire", ""),
                )
                if any(
                    str(title or "").strip().casefold() == normalized_oeuvre
                    for title in titles
                ):
                    return table_name, item
        return None

    def _citation_image_path(self, oeuvre, media_type=None):
        if not oeuvre:
            return None

        extensions = (".jpg", ".jpeg", ".png", ".webp")
        media_types = [table_name for _, table_name, _, _ in load_type_config()]
        if media_type in media_types:
            media_types.remove(media_type)
            media_types.insert(0, media_type)
        for table_name in media_types:
            base = image_filename(oeuvre, table_name)
            for extension in extensions:
                path = self.data_folder / f"{base}{extension}"
                if path.is_file():
                    return path

        base = sanitize_filename(oeuvre)
        for extension in extensions:
            path = self.data_folder / f"{base}{extension}"
            if path.is_file():
                return path
        return None

    def _create_citation_panel(self, items_by_type):
        citations = [
            citation
            for citation in self.db.get("citation", Citation)
            if str(citation.citation or "").strip()
        ]
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border-radius: 10px;
                border: 1px solid #3f3f46;
            }
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(24)

        if not citations:
            empty_label = QLabel("Aucune citation disponible")
            empty_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty_label, 1)
            panel.setMinimumHeight(140)
            return panel

        citation = random.choice(citations)
        work = self._find_citation_work(citation.oeuvre, items_by_type)
        image_title = (
            getattr(work[1], "titre", "") if work is not None else ""
        ) or citation.oeuvre
        image_path = self._citation_image_path(
            image_title,
            work[0] if work is not None else None,
        )
        if image_path:
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                image_label.setPixmap(
                    pixmap.scaled(180, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                layout.addWidget(image_label, 0, Qt.AlignVCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(10)

        quote_label = QLabel(citation.citation.strip())
        quote_label.setAlignment(Qt.AlignCenter)
        quote_label.setWordWrap(True)
        quote_label.setFont(QFont(quote_label.font().family(), 20, QFont.Bold))
        text_layout.addWidget(quote_label, 1)

        if work is not None:
            work_label = QLabel(citation.oeuvre.strip())
            work_label.setAlignment(Qt.AlignCenter)
            work_label.setFont(QFont(work_label.font().family(), 12))
            text_layout.addWidget(work_label)

            character = str(citation.personnage or "").strip()
            if character:
                character_label = QLabel(character)
                character_label.setAlignment(Qt.AlignCenter)
                character_label.setFont(QFont(character_label.font().family(), 11))
                text_layout.addWidget(character_label)
        else:
            artist = str(citation.artiste or "").strip()
            if artist:
                artist_label = QLabel(artist)
                artist_label.setAlignment(Qt.AlignCenter)
                artist_label.setFont(QFont(artist_label.font().family(), 11))
                text_layout.addWidget(artist_label)

        layout.addLayout(text_layout, 1)
        # panel.setMinimumHeight(280)
        return panel

    def refresh(self):
        if self.layout() is not None:
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(8, 8, 8, 8)

        summary_table = QTableWidget()
        headers = [
            "Type",
            "Épisodes\nvus",
            "Épisodes\nrestants",
            "Épisodes\ntotaux",
            "%\nEpisodes",
            "Œuvres\nvues",
            "Œuvres\nrestantes",
            "Œuvres\ntotales",
            "%\nOeuvres",
            "Note\nmoy",
            "Écart-\ntype",
            "Note\nmin",
            "Note\nmax",
            "1 Épisode\n%",
            "1 Oeuvre\n%",
            "Durée /\népisode\n(min)",
            "Temps\nvu",
            "Temps\nrestant",
            "Temps\ntotal",
        ]
        header = MultiLineHeader(Qt.Horizontal)
        summary_table.setHorizontalHeader(header)
        summary_table.setColumnCount(len(headers))
        summary_table.setHorizontalHeaderLabels(headers)
        summary_table.verticalHeader().setVisible(False)
        summary_table.setAlternatingRowColors(True)
        summary_table.setShowGrid(False)
        summary_table.setWordWrap(True)
        summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        summary_table.setSelectionMode(QTableWidget.NoSelection)
        summary_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        summary_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        summary_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        summary_table.horizontalHeader().setStretchLastSection(True)
        summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        summary_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        summary_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        rows = []
        type_config = load_type_config()
        items_by_type = {}
        for label, table_name, model_cls, avg_minutes in type_config:
            items = self.db.get(table_name, model_cls)
            items_by_type[table_name] = items
            rows.append(compute_type_stats(label, items, avg_minutes))

        totals = {
            "type": "Total",
            "Épisodes\nvus": sum(row["Épisodes\nvus"] for row in rows),
            "Épisodes\nrestants": sum(row["Épisodes\nrestants"] for row in rows),
            "Épisodes\ntotaux": sum(row["Épisodes\ntotaux"] for row in rows),
            "%\nEpisodes": str(round(100 * sum(row['Épisodes\nvus'] for row in rows) / sum(row['Épisodes\ntotaux'] for row in rows), 1) if sum(row['Épisodes\ntotaux'] for row in rows) else 0.0) + " %",
            "Œuvres\nvues": sum(row["Œuvres\nvues"] for row in rows),
            "Œuvres\nrestantes": sum(row["Œuvres\nrestantes"] for row in rows),
            "Œuvres\ntotales": sum(row["Œuvres\ntotales"] for row in rows),
            "%\nOeuvres": str(round(100 * sum(row['Œuvres\nvues'] for row in rows) / sum(row['Œuvres\ntotales'] for row in rows), 1) if sum(row['Œuvres\ntotales'] for row in rows) else 0.0) + " %",
            "Note\nmoy": str(round(sum(float(row['Note\nmoy']) for row in rows) / len(rows), 2) if rows else 0.0),
            "Écart-\ntype": "-",
            "Note\nmin": "-",
            "Note\nmax": "-",
            "1 Épisode\n%": round(sum(row["1 Épisode\n%"] for row in rows) / len(rows), 3) if rows else 0.0,
            "1 Oeuvre\n%": round(sum(row["1 Oeuvre\n%"] for row in rows) / len(rows), 3) if rows else 0.0,
            "Durée /\népisode\n(min)": "-",
            "Temps\nvu": _format_duration(sum(row["Épisodes\nvus"] for row in rows) * 25),
            "Temps\nrestant": _format_duration(sum(row["Épisodes\nrestants"] for row in rows) * 25),
            "Temps\ntotal": _format_duration(sum(row["Épisodes\ntotaux"] for row in rows) * 25),
        }
        rows.append(totals)

        summary_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, header in enumerate(headers):
                if header == "Type":
                    value = row.get("type", "")
                else:
                    value = row.get(header, "")
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                summary_table.setItem(row_idx, col_idx, item)
        content_layout.addWidget(summary_table)
        
        content_layout.addWidget(self._create_citation_panel(items_by_type))

        progress_group = QGroupBox("Répartition E et O réalisés")
        progress_layout = QGridLayout(progress_group)
        progress_layout.setSpacing(8)
        progress_layout.setContentsMargins(8, 8, 8, 8)

        for i, row in enumerate(rows[:-1]):
            progress_card = ProgressCard(
                row["type"],
                row["percent_e"],
                row["percent_o"]
            )

            progress_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            r = i % 3      # 3 lignes
            c = i // 3     # 2 colonnes
            progress_layout.addWidget(progress_card, r, c)

        # Les deux colonnes prennent la même largeur
        progress_layout.setColumnStretch(0, 1)
        progress_layout.setColumnStretch(1, 1)

        # Les trois lignes occupent toute la hauteur
        for i in range(3):
            progress_layout.setRowStretch(i, 1)

        pie_group = QGroupBox("Temps passé par type")
        pie_layout = QHBoxLayout(pie_group)
        pie_layout.setSpacing(16)

        values = [max(1, int(row["time_minutes"])) for row in rows[:-1]]
        colors = ["#4caf50", "#2196f3", "#ff9800", "#9c27b0", "#f44336", "#00bcd4", "#795548"]
        pie_widget = PieChartWidget(values, colors[:len(values)])
        pie_widget.setMinimumHeight(220)
        pie_layout.addWidget(pie_widget, 1)

        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(4)
        for label, value, color in zip([row["type"] for row in rows[:-1]], values, colors[:len(values)]):
            legend_item = QWidget()
            legend_item_layout = QHBoxLayout(legend_item)
            legend_item_layout.setContentsMargins(0, 0, 0, 0)
            color_label = QLabel()
            color_label.setFixedSize(12, 12)
            color_label.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
            legend_item_layout.addWidget(color_label)
            legend_item_layout.addWidget(QLabel(label))
            legend_layout.addWidget(legend_item)
        pie_layout.addLayout(legend_layout)
        
        bott_layout = QHBoxLayout()
        bott_layout.addWidget(progress_group, 7)
        bott_layout.addWidget(pie_group, 3)

        content_layout.addLayout(bott_layout)

        self.layout().addWidget(content_widget)
