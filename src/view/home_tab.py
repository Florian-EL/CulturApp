import json
import statistics
from pathlib import Path
from typing import List, Dict, Any

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QGroupBox, QWidget,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QSizePolicy, QFrame, QGridLayout
)

from src.models.film import Film
from src.models.manga import Manga
from src.models.roman import Roman
from src.models.serie import Serie
from src.models.serie_film import SerieFilm
from src.models.wattpad import Wattpad
from src.models.webtoon import Webtoon


MODEL_CLASSES = {
    "film": Film,
    "serie_film": SerieFilm,
    "serie": Serie,
    "roman": Roman,
    "manga": Manga,
    "webtoon": Webtoon,
    "wattpad": Wattpad,
}

def load_type_config() -> List[tuple]:
    return [
        ("Films", "film", Film, 120),
        ("Séries films", "serie_film", SerieFilm, 120),
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
    if label == "Séries films":
        value = getattr(item, "nom_serie", None)
    else:
        value = getattr(item, "titre", None)

    if value in (None, ""):
        value = getattr(item, "nom_serie", None)
    if value in (None, ""):
        value = getattr(item, "titre", None)

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

    work_keys = [
        _get_work_key(item, label)
        for item in items
        if _get_work_key(item, label)
        and _safe_int(getattr(item, "nb_ep_tot", 0)) != 0
    ]
    unique_work_keys = set(work_keys)
    works_total = len(unique_work_keys) or max(count, 1)

    works_seen = len({
        _get_work_key(item, label)
        for item in items
        if _safe_int(getattr(item, "nb_ep_res", 0)) == 0
        and _safe_int(getattr(item, "nb_vu", 0)) != 0
        and _get_work_key(item, label)
    })
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
        "1 Épisode": round(e_tot / count, 2) if count else 0.0,
        "1 Oeuvre": round(works_total / count, 2) if count else 0.0,
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
        self.setLayout(QVBoxLayout())
        self.refresh()

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
            "1 Épisode",
            "1 Oeuvre",
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
        for label, table_name, model_cls, avg_minutes in type_config:
            items = self.db.get(table_name, model_cls)
            rows.append(compute_type_stats(label, items, avg_minutes))

        totals = {
            "type": "Total",
            "Épisodes\nvus": sum(row["Épisodes\nvus"] for row in rows),
            "Épisodes\nrestants": sum(row["Épisodes\nrestants"] for row in rows),
            "Épisodes\ntotaux": sum(row["Épisodes\ntotaux"] for row in rows),
            "%\nEpisodes": f"{round(100 * sum(row["Épisodes\nvus"] for row in rows) / sum(row["Épisodes\ntotaux"] for row in rows), 1) if sum(row["Épisodes\ntotaux"] for row in rows) else 0.0:.1f}%",
            "Œuvres\nvues": sum(row["Œuvres\nvues"] for row in rows),
            "Œuvres\nrestantes": sum(row["Œuvres\nrestantes"] for row in rows),
            "Œuvres\ntotales": sum(row["Œuvres\ntotales"] for row in rows),
            "%\nOeuvres": f"{round(100 * sum(row['Œuvres\nvues'] for row in rows) / sum(row['Œuvres\ntotales'] for row in rows), 1) if sum(row['Œuvres\ntotales'] for row in rows) else 0.0:.1f}%",
            "Note\nmoy": f"{round(sum(float(row['Note\nmoy']) for row in rows) / len(rows), 2) if rows else 0.0:.2f}",
            "Écart-\ntype": "-",
            "Note\nmin": "-",
            "Note\nmax": "-",
            "1 Épisode": round(sum(row["1 Épisode"] for row in rows) / len(rows), 2) if rows else 0.0,
            "1 Oeuvre": round(sum(row["1 Oeuvre"] for row in rows) / len(rows), 2) if rows else 0.0,
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
        summary_table.setMinimumHeight(350)
        content_layout.addWidget(summary_table)

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
