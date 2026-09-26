from dataclasses import dataclass


@dataclass
class Citation:
    id: int = 0
    citation: str = ""
    oeuvre: str = ""
    personnage: str = ""
    artiste: str = ""
