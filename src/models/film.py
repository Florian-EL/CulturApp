from dataclasses import dataclass

@dataclass
class Film:
    id    : int = 0
    titre : str = ""
    note  : int = 0