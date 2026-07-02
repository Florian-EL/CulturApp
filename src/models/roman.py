from dataclasses import dataclass

@dataclass
class Roman:
    id        : int = 0
    titre     : str = ""
    auteur    : str = ""
    type      : str = ""
    genre     : str = ""
    possede   : str = ""
    nb_ep_vu  : int = 0
    nb_ep_res : int = 0
    nb_ep_tot : int = 0
    updated   : str = ""
    etat      : str = ""
    note      : float = 0
    nb_vu     : int = 0