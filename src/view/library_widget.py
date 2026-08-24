from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    Qt,
    QTimer,
    QVariantAnimation,
)
from PySide6.QtGui import QCursor, QPainter, QPixmap, QTransform
from PySide6.QtWidgets import (
    QApplication,
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


class WorkPreview(QFrame):
    """Floating preview displayed when hovering a book spine."""

    def __init__(self, work, image_path, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet("""
            QFrame {
                background: #202020;
                border: 1px solid #555555;
                border-radius: 10px;
            }
            QLabel {
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        cover = QLabel()
        cover.setFixedSize(120, 175)
        cover.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(str(image_path)) if image_path else QPixmap()
        if not pixmap.isNull():
            cover.setPixmap(
                pixmap.scaled(cover.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            cover.setText("Pas de\ncouverture")
            cover.setStyleSheet("background: #303030; color: #777777; border-radius: 5px;")
        layout.addWidget(cover)

        info = QVBoxLayout()
        info.setSpacing(5)

        title = QLabel(str(work.titre))
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        info.addWidget(title)

        author = getattr(work, "auteur", "") or getattr(work, "vo", "")
        if author:
            label = QLabel(str(author))
            label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
            label.setWordWrap(True)
            info.addWidget(label)

        metadata = []
        for field in ("genre", "type", "etat"):
            value = getattr(work, field, "")
            if value:
                metadata.append(str(value))
        if metadata:
            details = QLabel(" • ".join(metadata))
            details.setWordWrap(True)
            details.setStyleSheet("color: #888888; font-size: 11px;")
            info.addWidget(details)

        info.addStretch()
        layout.addLayout(info)
        self.adjustSize()


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


class BookSpine(QFrame):
    """Small book seen from the side, with a floating preview on hover."""

    def __init__(self, work, image_path, parent=None):
        super().__init__(parent)

        self.work = work
        self.image_path = image_path
        self.preview = None

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._hide_preview)

        # ---------------------------------------------------------
        # Box
        # ---------------------------------------------------------

        self.setFixedSize(38, 155)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(str(work.titre))

        self.setStyleSheet("""
            QFrame {
                background: #303030;
                border: 1px solid #444444;
                border-radius: 3px;
            }

            QFrame:hover {
                background: #3b3b3b;
                border: 1px solid #777777;
            }
        """)

        # ---------------------------------------------------------
        # Layout
        # ---------------------------------------------------------

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)

        # ---------------------------------------------------------
        # Title
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
        # Image
        # ---------------------------------------------------------

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignBottom)
        self.image_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.image_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        layout.addWidget(self.image_label)


        # Initial rendering
        self._update_image()

    # =============================================================
    # Events
    # =============================================================

    def enterEvent(self, event):
        self.hide_timer.stop()
        self._show_preview()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hide_timer.start(180)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._show_preview()

        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_image()

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

        # Rotate the cover so that it follows
        # the orientation of the book spine.
        pixmap = pixmap.transformed(
            QTransform().rotate(-90),
            Qt.SmoothTransformation,
        )

        # Scale according to the actual QLabel size.
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image_label.setPixmap(scaled)

    # =============================================================
    # Preview
    # =============================================================

    def _show_preview(self):
        if self.preview is None:
            self.preview = WorkPreview(
                self.work,
                self.image_path,
            )

        self.preview.adjustSize()

        cursor = QCursor.pos()

        screen = QApplication.screenAt(cursor)

        if screen is None:
            screen = QApplication.primaryScreen()

        available = screen.availableGeometry()

        # Default position:
        # right of the cursor and slightly above it.
        x = cursor.x() + 18
        y = cursor.y() - self.preview.height() - 10

        # If it doesn't fit on the right,
        # put it on the left.
        if x + self.preview.width() > available.right():
            x = cursor.x() - self.preview.width() - 18

        # If it doesn't fit above,
        # put it below the cursor.
        if y < available.top():
            y = cursor.y() + 18

        # Keep the preview inside the screen vertically.
        if y + self.preview.height() > available.bottom():
            y = available.bottom() - self.preview.height()

        self.preview.move(x, y)
        self.preview.show()
        self.preview.raise_()

    def _hide_preview(self):
        if (
            self.preview is not None
            and not self.preview.underMouse()
        ):
            self.preview.hide()





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

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform
        )

        self.setAlignment(
            Qt.AlignCenter
        )

        self.setStyleSheet(
            """
            QGraphicsView {
                background: transparent;
                border: none;
            }
            """
        )

        # La scène occupe toute la zone visible.
        self.scene.setSceneRect(
            0,
            0,
            self.viewport().width(),
            self.viewport().height()
        )

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def _create_items(self):

        for widget in self.widgets:

            proxy = QGraphicsProxyWidget()
            proxy.setWidget(widget)

            # Le centre de transformation est le centre
            # du widget : indispensable pour le scale.
            proxy.setTransformOriginPoint(
                proxy.boundingRect().center()
            )

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
            importance = max(
                0.0,
                1.0 - distance / 3.0
            )

            scale = (
                self.min_scale
                + (
                    self.max_scale
                    - self.min_scale
                ) * importance
            )

            opacity = (
                self.min_opacity
                + (
                    self.max_opacity
                    - self.min_opacity
                ) * importance
            )

            # ----------------------------------------------------------
            # Position horizontale
            # ----------------------------------------------------------

            x = (
                center_x
                + relative * self.spacing
            )

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

            item.setZValue(
                1000 - distance
            )

            # Le widget est centré sur sa position.
            rect = item.boundingRect()

            item.setPos(
                x - rect.width() / 2,
                y - rect.height() / 2
            )

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

        target = round(
            self.offset
        ) + direction

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

        animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        animation.valueChanged.connect(
            self._animation_value_changed
        )

        animation.finished.connect(
            self._animation_finished
        )

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
        #
        # Exemple :
        #
        # A B C D E
        #
        # offset = 5
        #
        # devient :
        #
        # offset = 0
        #
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

        self.scene.setSceneRect(
            0,
            0,
            self.viewport().width(),
            self.viewport().height()
        )

        self._update_positions()


class LibraryWidgets(QWidget):
    def __init__(self, db, data_folder=None):
        super().__init__()
        self.db = db
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
        self._build_ui()
        self.refresh()

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
        layout.setContentsMargins(
            0,
            40,
            0,
            40
        )

        previews = []

        for room_type, room_info in self.rooms.items():

            title, _, _ = room_info

            preview = self._create_room_preview(
                title,
                room_type,
                self._get_room_data(room_type)[:6],
            )

            previews.append(preview)

        carousel = RoomCarousel(
            previews,
            widget
        )

        layout.addWidget(carousel)

        return widget

    # ================================================================
    # ROOM PREVIEW
    # ================================================================

    def _create_room_preview(self, title, room_type, works):
        room = QFrame()
        room.setMinimumSize(280, 430)
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
        for i, work in enumerate(works[:6]):
            cover = self._create_preview_cover(work)
            preview_layout.addWidget(cover, i // 3, i % 3)
        layout.addWidget(preview)
        layout.addStretch()
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
        widget.grid.setContentsMargins(30, 30, 30, 30)
        widget.grid.setSpacing(28)
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
        _, table, model_cls = self.rooms[room_type]
        try:
            return list(self.db.get(table, model_cls) or [])
        except (AttributeError, TypeError, ValueError):
            return []

    # ================================================================
    # ENTER ROOM
    # ================================================================

    def _enter_room(self, room):
        self._update_room_filters(room)
        self.stack.setCurrentWidget(self.room_widgets[room])

    # ================================================================
    # FILTERS
    # ================================================================

    def _update_room_filters(self, room_type):
        widget = self.room_widgets[room_type]
        works = self._get_room_data(room_type)
        types = sorted(
            {
                str(work.type)
                for work in works
                if work.type
            }
        )
        genres = sorted(
            {
                str(work.genre)
                for work in works
                if work.genre
            }
        )
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
            if (
                selected_type != "Tous les types"
                and str(work.type) != selected_type
            ):
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
        self._clear_layout(widget.grid)

        # A shelf contains a horizontal row of books.
        available_width = max(300, widget.container.width() - 60)
        books_per_row = max(1, available_width // 23)

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

            for work in works[start:start + books_per_row]:
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

    def refresh(self):
        for room_type in self.room_widgets:
            self._update_room_filters(room_type)
            self._refresh_room(room_type)
