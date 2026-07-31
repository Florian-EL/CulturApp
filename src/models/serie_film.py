from dataclasses import dataclass

@dataclass
class SerieFilm:
    id        : int = 0
    nom_serie : str = ""
    film      : str = ""
    titre     : str = ""
    type      : str = ""
    genre     : str = ""
    vo        : str = ""
    cinema    : bool = 0
    updated   : str = ""
    etat      : str = ""
    annee_vu  : int = 0
    nb_vu     : int = 0
    note      : float = 0
    sortie    : str = ""
    nb_ep_vu  : int = 0
    nb_ep_res : int = 0
    nb_ep_tot : int = 0
    notice    : str = ""

