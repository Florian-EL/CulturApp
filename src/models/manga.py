from dataclasses import dataclass

@dataclass
class Manga:
    id    : int = 0
    titre : str = ""
    note  : float = 0