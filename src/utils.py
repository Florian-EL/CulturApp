import unicodedata
from enum import Enum


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)

        if item.widget():
            item.widget().deleteLater()

        elif item.layout():
            clear_layout(item.layout())


def normalize_field_key(value):
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return "".join(ch for ch in text if ch.isalnum())


def resolve_field_options(field_options, column_name):
    if not field_options:
        return []

    if column_name in field_options:
        return field_options[column_name]

    normalized_column = normalize_field_key(column_name)
    for key, options in field_options.items():
        if normalize_field_key(key) == normalized_column:
            return options

    return []


class MediaType(Enum):
    FILM = "film"
    SERIEFILM = "serie_film"
    SERIE = "serie"
    ROMAN = "roman"
    MANGA = "manga"
    WEBTOON = "webtoon"
    WATTPAD = "wattpad"
