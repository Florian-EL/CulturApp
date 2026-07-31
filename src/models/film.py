from dataclasses import dataclass

@dataclass
class Film:
    id        : int = 0
    titre     : str = ""
    type      : str = ""
    genre     : str = ""
    vo        : str = ""
    cinema    : str = ""
    updated   : str = ""
    etat      : str = ""
    annee_vu  : str = ""
    nb_vu     : int = 0
    note      : float = 0
    sortie    : str = ""
    nb_ep_vu  : int = 0
    nb_ep_res : int = 0
    nb_ep_tot : int = 0
    notice    : str = ""
