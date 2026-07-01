from dataclasses import dataclass

@dataclass
class Wattpad:
    id        : int = 0
    titre     : str = ""
    auteur    : str = ""
    type      : str = ""
    genre     : str = ""
    nb_ep_lu  : int = 0
    nb_ep_res : int = 0
    nb_ep_tot : int = 0
    updated   : str = ""
    etat      : str = ""
    nb_vu     : int = 0
    note      : float = 0