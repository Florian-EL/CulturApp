import multiprocessing
import random
from pathlib import Path
from queue import Empty

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QTimer,
    QVariantAnimation,
)
from PySide6.QtGui import QPainter, QPixmap, QTransform
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsProxyWidget,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.film import Film
from src.models.manga import Manga
from src.models.roman import Roman
from src.models.serie import Serie
from src.models.serie_film import SerieFilm
from src.models.wattpad import Wattpad
from src.models.webtoon import Webtoon
from src.services.database_manager import load_tables_for_display


class BookSpine(QFrame):
    """Book spine that expands to reveal its full cover and metadata."""

    def __init__(self, work, image_path, parent=None):
        super().__init__(parent)

        self.work = work
        self.image_path = image_path

        # ---------------------------------------------------------
        # Dimensions
        # ---------------------------------------------------------

        self.normal_width = 38
        self.expanded_width = 100

        self.book_height = 202
        self.info_height = 70

        self.setFixedSize(self.normal_width, self.book_height)

        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(str(work.titre))

        # ---------------------------------------------------------
        # Style
        # ---------------------------------------------------------

        self.setStyleSheet("""
            QFrame {
                background: #303030;
                border: 1px solid #444444;
                border-radius: 3px;
            }
        """)

        # ---------------------------------------------------------
        # Main layout
        # ---------------------------------------------------------

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        self.layout = layout

        # ---------------------------------------------------------
        # Title - normal view
        # ---------------------------------------------------------

        self.title_label = RotatedLabel(str(self.work.titre))

        self.title_label.setWordWrap(True)

        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                border: none;
                font-size: 8pt;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.title_label)

        # ---------------------------------------------------------
        # Cover
        # ---------------------------------------------------------

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.image_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        layout.addWidget(self.image_label, 1)

        # ---------------------------------------------------------
        # Metadata - expanded view
        # ---------------------------------------------------------

        self.info_label = QLabel()

        self.info_label.setFixedHeight(self.info_height)
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.info_label.setStyleSheet("""
            QLabel {
                color: white;
                background: #252525;
                border: none;
                padding: 4px;
                font-size: 8pt;
            }
        """)

        self.info_label.setText(self._metadata_text())

        layout.addWidget(self.info_label)

        # Hidden in normal state
        self.info_label.hide()

        # ---------------------------------------------------------
        # Image
        # ---------------------------------------------------------

        self._update_image()

        # ---------------------------------------------------------
        # Animation
        # ---------------------------------------------------------

        self.animation = QPropertyAnimation(self, b"minimumWidth")

        self.animation.setDuration(180)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        self.animation.valueChanged.connect(self._animation_width_changed)

    # =============================================================
    # Events
    # =============================================================

    def enterEvent(self, event):
        self._expand()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._collapse()
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_image()

    # =============================================================
    # Expand / collapse
    # =============================================================

    def _expand(self):

        self.animation.stop()

        # Le titre vertical disparaît
        self.title_label.hide()

        # Le texte devient un vrai élément
        # du layout et prend donc sa place.
        self.info_label.show()

        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.expanded_width)

        self.animation.start()

    def _collapse(self):

        self.animation.stop()

        # Retire le bloc d'informations
        self.info_label.hide()

        # Rend le titre vertical
        self.title_label.show()

        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.normal_width)

        self.animation.start()

    def _animation_width_changed(self, width):

        self.setFixedWidth(int(width))

        # Force le parent à recalculer
        # la position des livres voisins.
        if self.parentWidget():
            self.parentWidget().updateGeometry()

        self._update_image()

    # =============================================================
    # Metadata
    # =============================================================

    def _metadata_text(self):

        lines = [f"<b>{self.work.titre}</b>"]

        note = getattr(self.work, "note", None)

        if note not in (None, "", 0, "0", 0.0, "0.0"):
            lines.append(f"Note : {note}/10")

        return "<br>".join(lines)

    # =============================================================
    # Image
    # =============================================================

    def _update_image(self):

        if not self.image_path:
            self.image_label.clear()
            return

        pixmap = QPixmap(str(self.image_path))

        if pixmap.isNull():
            self.image_label.clear()
            return

        # ---------------------------------------------------------
        # Expanded view
        # ---------------------------------------------------------

        scaled = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        self.image_label.setPixmap(scaled)


class RotatedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(12)
        self.setMaximumWidth(38)
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)

    def sizeHint(self):
        hint = super().sizeHint()
        return hint.transposed()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)

        painter.translate(0, self.height())
        painter.rotate(-90)

        painter.drawText(
            0,
            0,
            self.height(),
            self.width(),
            Qt.AlignLeft | Qt.TextWordWrap,
            self.text(),
        )


class RoomCarousel(QGraphicsView):
    """
    Horizontal infinite carousel.

    - Navigation uniquement à la roulette.
    - Les éléments tournent de manière circulaire.
    - L'élément central est le plus important.
    - Les éléments latéraux sont progressivement réduits.
    """

    def __init__(self, widgets, parent=None):
        super().__init__(parent)

        self.widgets = widgets
        self.items = []

        # Position virtuelle du carousel.
        # Peut être non entière pendant une animation.
        self.offset = 0.0

        # Configuration visuelle
        self.spacing = 280
        self.max_scale = 1.0
        self.min_scale = 0.55

        self.max_opacity = 1.0
        self.min_opacity = 0.35

        self.rotation = 4.0

        # Animation
        self.animation = None

        self._setup_view()
        self._create_items()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_view(self):

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setFrameShape(QGraphicsView.NoFrame)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        self.setAlignment(Qt.AlignCenter)

        self.setStyleSheet(
            """
            QGraphicsView {
                background: transparent;
                border: none;
            }
            """
        )

        # La scène occupe toute la zone visible.
        self.scene.setSceneRect(0, 0, self.viewport().width(), self.viewport().height())

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def _create_items(self):

        for widget in self.widgets:
            proxy = QGraphicsProxyWidget()
            proxy.setWidget(widget)

            # Le centre de transformation est le centre
            # du widget : indispensable pour le scale.
            proxy.setTransformOriginPoint(proxy.boundingRect().center())

            self.scene.addItem(proxy)
            self.items.append(proxy)

        self._update_positions()

    # ------------------------------------------------------------------
    # Carousel mathematics
    # ------------------------------------------------------------------

    def _circular_distance(self, index):
        """
        Distance signée entre un élément et le centre.

        Exemple avec 5 éléments :

            offset = 0

            A ->  0
            B ->  1
            C ->  2
            D -> -2
            E -> -1
        """

        count = len(self.items)

        if count == 0:
            return 0

        distance = index - self.offset

        # Ramène la distance dans l'intervalle circulaire.
        while distance > count / 2:
            distance -= count

        while distance < -count / 2:
            distance += count

        return distance

    def _update_positions(self):

        if not self.items:
            return

        viewport_width = self.viewport().width()
        viewport_height = self.viewport().height()

        center_x = viewport_width / 2
        center_y = viewport_height / 2

        for index, item in enumerate(self.items):
            relative = self._circular_distance(index)
            distance = abs(relative)

            # ----------------------------------------------------------
            # Importance
            # ----------------------------------------------------------

            # 1 au centre
            # 0 sur les côtés
            importance = max(0.0, 1.0 - distance / 3.0)

            scale = self.min_scale + (self.max_scale - self.min_scale) * importance

            opacity = (
                self.min_opacity + (self.max_opacity - self.min_opacity) * importance
            )

            # ----------------------------------------------------------
            # Position horizontale
            # ----------------------------------------------------------

            x = center_x + relative * self.spacing

            y = center_y

            # ----------------------------------------------------------
            # Rotation légère
            # ----------------------------------------------------------

            rotation = -relative * self.rotation

            # ----------------------------------------------------------
            # Application
            # ----------------------------------------------------------

            item.setScale(scale)
            item.setOpacity(opacity)
            item.setRotation(rotation)

            item.setZValue(1000 - distance)

            # Le widget est centré sur sa position.
            rect = item.boundingRect()

            item.setPos(x - rect.width() / 2, y - rect.height() / 2)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def wheelEvent(self, event):

        if not self.items:
            return

        delta = event.angleDelta().y()

        if delta == 0:
            return

        # Roulette vers le bas -> élément suivant
        # Roulette vers le haut -> élément précédent
        if delta < 0:
            direction = 1
        else:
            direction = -1

        target = round(self.offset) + direction

        self._animate_to(target)

        event.accept()

    def _animate_to(self, target):

        if self.animation is not None:
            self.animation.stop()

        start = self.offset

        # --------------------------------------------------------------
        # Évite les gros déplacements artificiels.
        #
        # Exemple :
        #
        # A B C D E
        # offset = 4
        # next = 5
        #
        # On garde 5 comme position virtuelle.
        # Le modulo est appliqué uniquement au calcul visuel.
        # --------------------------------------------------------------

        animation = QVariantAnimation(self)

        animation.setStartValue(start)
        animation.setEndValue(float(target))

        animation.setDuration(400)

        animation.setEasingCurve(QEasingCurve.OutCubic)

        animation.valueChanged.connect(self._animation_value_changed)

        animation.finished.connect(self._animation_finished)

        self.animation = animation
        animation.start()

    def _animation_value_changed(self, value):

        self.offset = float(value)

        self._update_positions()

    def _animation_finished(self):

        if not self.items:
            return

        count = len(self.items)

        # --------------------------------------------------------------
        # On remet offset dans une plage raisonnable.
        # Exemple :
        # A B C D E
        # offset = 5
        # devient :
        # offset = 0
        # Visuellement rien ne change.
        # --------------------------------------------------------------

        self.offset %= count

        self._update_positions()

        self.animation = None

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def resizeEvent(self, event):

        super().resizeEvent(event)

        self.scene.setSceneRect(0, 0, self.viewport().width(), self.viewport().height())

        self._update_positions()


class LibraryWidgets(QWidget):
    def __init__(self, db, data_folder=None):
        super().__init__()
        self.db = db
        self._data_loaded = False
        self._data_loading = False
        self._data_process = None
        self._data_queue = None
        self._data_cache = {}
        self.data_folder = Path(data_folder).expanduser() if data_folder else Path(".")
        self.setMinimumSize(800, 600)
        self.rooms = {
            "film": ("Films", "film", Film),
            "serie_film": ("Films de séries", "serie_film", SerieFilm),
            "serie": ("Séries", "serie", Serie),
            "roman": ("Romans", "roman", Roman),
            "manga": ("Mangas", "manga", Manga),
            "webtoon": ("Webtoons", "webtoon", Webtoon),
            "wattpad": ("Wattpad", "wattpad", Wattpad),
        }
        self.room_widgets = {}
        self._room_columns = {}
        self._build_ui()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._data_loaded:
            self._schedule_initial_load()

    def _schedule_initial_load(self):
        if self._data_loaded:
            return
        QTimer.singleShot(100, self._load_initial_data)

    def _load_initial_data(self):
        if self._data_loaded:
            return
        self.refresh()

    def _start_data_load(self):
        if self._data_loading:
            return

        self._data_loading = True
        context = multiprocessing.get_context("spawn")
        self._data_queue = context.Queue()
        self._data_process = context.Process(
            target=load_tables_for_display,
            args=(
                str(self.db.db_path),
                [room[1] for room in self.rooms.values()],
                self._data_queue,
            ),
        )
        self._data_process.start()
        QTimer.singleShot(15, self._poll_data_load)

    def _poll_data_load(self):
        if self._data_queue is None:
            return

        try:
            rows_by_table = self._data_queue.get_nowait()
        except Empty:
            if self._data_process is not None and self._data_process.is_alive():
                QTimer.singleShot(15, self._poll_data_load)
                return
            rows_by_table = {}

        self._data_cache = {}
        for room_type, (_, table, model_cls) in self.rooms.items():
            self._data_cache[room_type] = [
                self.db.row_to_model(model_cls, row)
                for row in rows_by_table.get(table, [])
            ]

        if self._data_process is not None:
            self._data_process.join()
        self._data_process = None
        self._data_queue.close()
        self._data_queue = None
        self._data_loading = False
        self._data_loaded = True
        self.refresh_display()

    # ================================================================
    # UI
    # ================================================================

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        # ------------------------------------------------------------
        # Hall
        # ------------------------------------------------------------
        self.hall = self._create_hall()
        self.stack.addWidget(self.hall)
        for room_type in self.rooms:
            room_widget = self._create_room(room_type)
            self.room_widgets[room_type] = room_widget
            self.stack.addWidget(room_widget)
        self.main_layout.addWidget(self.stack)

    # ================================================================
    # HALL
    # ================================================================

    def _create_hall(self):

        widget = QWidget()

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 40, 0, 40)

        previews = []

        for room_type, room_info in self.rooms.items():
            title, _, _ = room_info
            works = self._select_preview_works(self._get_room_data(room_type))

            preview = self._create_room_preview(
                title,
                room_type,
                works,
            )

            previews.append(preview)

        carousel = RoomCarousel(previews, widget)

        layout.addWidget(carousel)

        return widget

    @staticmethod
    def _note_value(work):
        try:
            return float(getattr(work, "note", 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _select_preview_works(cls, works, limit=9):
        works_by_note = {}
        for work in works:
            works_by_note.setdefault(cls._note_value(work), []).append(work)

        selected = []
        for note in sorted(works_by_note, reverse=True):
            note_works = works_by_note[note]
            remaining = limit - len(selected)
            if remaining <= 0:
                break
            selected.extend(random.sample(note_works, min(remaining, len(note_works))))

        return selected

    # ================================================================
    # ROOM PREVIEW
    # ================================================================

    def _create_room_preview(self, title, room_type, works):
        room = QFrame()
        room.setMinimumSize(300, 600)
        room.setStyleSheet("""
            QFrame {
                background: #202020;
                border: 1px solid #333333;
                border-radius: 12px;
            }
            QFrame:hover {
                background: #282828;
                border: 1px solid #555555;
            }
        """)
        layout = QVBoxLayout(room)
        layout.setContentsMargins(15, 15, 15, 20)
        # ------------------------------------------------------------
        # Nom de salle
        # ------------------------------------------------------------
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 21px;
            font-weight: bold;
            border: none;
        """)
        layout.addWidget(label)
        # ------------------------------------------------------------
        # Aperçu intérieur
        # ------------------------------------------------------------
        preview = QFrame()
        preview.setStyleSheet("""
            QFrame {
                background: #151515;
                border: none;
                border-radius: 8px;
            }
        """)
        preview_layout = QGridLayout(preview)
        preview_layout.setContentsMargins(20, 25, 20, 20)
        preview_layout.setSpacing(8)
        # Quelques couvertures
        for i, work in enumerate(works[:9]):
            cover = self._create_preview_cover(work)
            preview_layout.addWidget(cover, i // 3, i % 3)
        layout.addWidget(preview)
        
        hint = QLabel("Entrer dans la salle →")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("""
            color: #777777;
            border: none;
        """)
        layout.addWidget(hint)
        room.mousePressEvent = lambda event, r=room_type: self._enter_room(r)
        return room

    # ================================================================
    # PREVIEW COVER
    # ================================================================

    def _create_preview_cover(self, work):
        label = QLabel()
        label.setFixedSize(65, 95)
        label.setAlignment(Qt.AlignCenter)
        title = str(work.titre)
        cover_path = self._image_path(work)
        if cover_path:
            pixmap = QPixmap(str(cover_path))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                label.setPixmap(pixmap)
                return label
        # Placeholder
        label.setText(title[:12])
        label.setWordWrap(True)
        label.setStyleSheet("""
            background: #303030;
            color: #888888;
            border-radius: 4px;
            font-size: 9px;
        """)
        return label

    # ================================================================
    # ROOM
    # ================================================================

    def _create_room(self, room_type):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # ------------------------------------------------------------
        # Header
        # ------------------------------------------------------------
        header = QHBoxLayout()
        back = QPushButton("← Bibliothèque")
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.hall))
        title = QLabel(self.rooms[room_type][0])
        title.setStyleSheet("""
            font-size: 25px;
            font-weight: bold;
        """)
        widget.search = QLineEdit()
        widget.search.setPlaceholderText("Rechercher...")
        widget.type_filter = QComboBox()
        widget.type_filter.addItem("Tous les types")
        widget.genre_filter = QComboBox()
        widget.genre_filter.addItem("Tous les genres")
        header.addWidget(back)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(widget.search)
        header.addWidget(widget.type_filter)
        header.addWidget(widget.genre_filter)
        layout.addLayout(header)
        # ------------------------------------------------------------
        # Œuvres
        # ------------------------------------------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget.container = QWidget()
        widget.grid = QVBoxLayout(widget.container)
        widget.grid.setContentsMargins(10, 10, 10, 10)
        widget.grid.setSpacing(20)
        scroll.setWidget(widget.container)
        layout.addWidget(scroll)
        # ------------------------------------------------------------
        # Signals
        # ------------------------------------------------------------
        widget.search.textChanged.connect(lambda: self._refresh_room(room_type))
        widget.type_filter.currentTextChanged.connect(
            lambda: self._refresh_room(room_type)
        )
        widget.genre_filter.currentTextChanged.connect(
            lambda: self._refresh_room(room_type)
        )
        return widget

    # ================================================================
    # DATABASE
    # ================================================================

    def _get_room_data(self, room_type):
        return self._data_cache.get(room_type, [])

    # ================================================================
    # ENTER ROOM
    # ================================================================

    def _enter_room(self, room):
        self._update_room_filters(room)
        widget = self.room_widgets[room]
        self.stack.setCurrentWidget(widget)
        QTimer.singleShot(0, lambda: self._refresh_room(room))

    # ================================================================
    # FILTERS
    # ================================================================

    def _update_room_filters(self, room_type):
        widget = self.room_widgets[room_type]
        works = self._get_room_data(room_type)
        types = sorted({str(work.type) for work in works if work.type})
        genres = sorted({str(work.genre) for work in works if work.genre})
        widget.type_filter.blockSignals(True)
        widget.genre_filter.blockSignals(True)
        widget.type_filter.clear()
        widget.type_filter.addItem("Tous les types")
        widget.type_filter.addItems(types)
        widget.genre_filter.clear()
        widget.genre_filter.addItem("Tous les genres")
        widget.genre_filter.addItems(genres)
        widget.type_filter.blockSignals(False)
        widget.genre_filter.blockSignals(False)

    # ================================================================
    # REFRESH
    # ================================================================

    def _refresh_room(self, room_type):
        widget = self.room_widgets[room_type]
        query = widget.search.text().strip().lower()
        selected_type = widget.type_filter.currentText()
        selected_genre = widget.genre_filter.currentText()
        works = []
        for work in self._get_room_data(room_type):
            searchable = " ".join(
                str(getattr(work, field, ""))
                for field in ("titre", "auteur", "nom_serie", "vo", "genre", "type")
            ).lower()
            if query and query not in searchable:
                continue
            if selected_type != "Tous les types" and str(work.type) != selected_type:
                continue
            if (
                selected_genre != "Tous les genres"
                and str(work.genre) != selected_genre
            ):
                continue
            works.append(work)
        self._display_works(widget, works)

    # ================================================================
    # DISPLAY WORKS
    # ================================================================

    def _display_works(self, widget, works):
        available_width = max(300, widget.container.width() - 60)

        book_width = 38
        spacing = 7

        books_per_row = (
            max(1, int((available_width + spacing) / (book_width + spacing))) - 1
        )

        room_type = next(
            (
                room
                for room, room_widget in self.room_widgets.items()
                if room_widget is widget
            ),
            None,
        )

        if room_type is not None:
            self._room_columns[room_type] = books_per_row

        self._clear_layout(widget.grid)

        for start in range(0, len(works), books_per_row):
            row = QFrame()
            row.setMinimumHeight(190)
            row.setStyleSheet("""
                QFrame {
                    background: transparent;
                    border: none;
                }
            """)

            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(8, 0, 8, 0)
            row_layout.setSpacing(0)

            books_layout = QHBoxLayout()
            books_layout.setContentsMargins(0, 0, 0, 0)
            books_layout.setSpacing(7)
            books_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

            for work in works[start : start + books_per_row]:
                spine = self._create_work_spine(work)
                books_layout.addWidget(spine, alignment=Qt.AlignBottom)

            row_layout.addLayout(books_layout)
            row_layout.addSpacing(7)

            # Wooden shelf underneath the books.
            shelf = QFrame()
            shelf.setFixedHeight(12)
            shelf.setStyleSheet("""
                QFrame {
                    background: #4a3525;
                    border: 1px solid #60452f;
                    border-radius: 2px;
                }
            """)
            row_layout.addWidget(shelf)

            widget.grid.addWidget(row)

        widget.grid.addStretch()

    # ================================================================
    # WORK SPINE
    # ================================================================

    def _create_work_spine(self, work):
        return BookSpine(work, self._image_path(work))

    # ================================================================
    # COVER
    # ================================================================

    def _set_cover(self, label, path):
        cover_path = self._cover_path(path)
        if cover_path:
            pixmap = QPixmap(str(cover_path))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                label.setPixmap(pixmap)
                return
        label.setText("Pas de couverture")
        label.setStyleSheet("""
            background: #303030;
            color: #777777;
            border-radius: 5px;
        """)

    def _cover_path(self, path):
        if not path:
            return None
        candidate = Path(str(path)).expanduser()
        if not candidate.is_absolute():
            candidate = self.data_folder / candidate
        return candidate if candidate.exists() else None

    def _image_path(self, work):
        title = str(work.titre)
        base = self._sanitize_filename(title)
        for extension in (".jpg", ".jpeg", ".png", ".webp"):
            candidate = self.data_folder / (base + extension)
            if candidate.exists():
                return str(candidate)
        notice = work.notice
        return str(self._cover_path(notice)) if self._cover_path(notice) else None

    @staticmethod
    def _sanitize_filename(name):
        for character in ("/", "\\", ":", "*", "?", '"', "<", ">", "|"):
            name = name.replace(character, "_")
        return name.strip()

    # ================================================================
    # UTILS
    # ================================================================

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    # ================================================================
    # PUBLIC REFRESH
    # ================================================================

    def refresh_display(self):
        current_widget = self.stack.currentWidget()
        was_hall_active = current_widget is self.hall
        hall_index = self.stack.indexOf(self.hall)
        self.stack.removeWidget(self.hall)
        self.hall.deleteLater()
        self.hall = self._create_hall()
        self.stack.insertWidget(hall_index, self.hall)
        for room_type in self.room_widgets:
            self._update_room_filters(room_type)
            self._refresh_room(room_type)
        if was_hall_active:
            self.stack.setCurrentWidget(self.hall)
        elif current_widget is not None:
            self.stack.setCurrentWidget(current_widget)

    def refresh(self):
        """Reload library data without blocking the Qt event loop."""
        self._start_data_load()

    def closeEvent(self, event):
        if self._data_process is not None and self._data_process.is_alive():
            self._data_process.terminate()
            self._data_process.join()
        if self._data_queue is not None:
            self._data_queue.close()
            self._data_queue = None
        super().closeEvent(event)
