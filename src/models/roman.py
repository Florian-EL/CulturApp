from dataclasses import dataclass

@dataclass
class Roman:
    id        : int = 0
    titre     : str = ""
    auteur    : str = ""
    type      : str = ""
    vo        : str = ""
    genre     : str = ""
    lu_suite  : str = ""
    ep_deb    : int = 0
    ep_act    : int = 0
    nb_ep_lu  : int = 0
    nb_ep_res : int = 0
    nb_ep_tot : int = 0
    updated   : str = ""
    etat      : str = ""
    note      : float = 0
    nb_vu     : int = 0
    site      : str = ""