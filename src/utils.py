from enum import Enum

def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)

        if item.widget():
            item.widget().deleteLater()

        elif item.layout():
            clear_layout(item.layout())

class MediaType(Enum):
    FILM = "film"
    SERIEFILM = "serie_film"
    ROMAN = "roman"
