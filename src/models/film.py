from dataclasses import dataclass

@dataclass
class Film:
    id       : int = 0
    titre    : str = ""
    type     : str = ""
    genre    : str = ""
    vo       : str = ""
    cinema   : bool = 0
    updated  : str = ""
    etat     : str = ""
    annee_vu : int = 0
    nb_vu    : int = 0
    note     : int = 0

