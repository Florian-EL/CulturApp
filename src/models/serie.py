from dataclasses import dataclass

@dataclass
class Serie:
    id          : int = 0
    titre       : str = ""
    type        : str = ""
    genre       : str = ""
    vo          : str = ""
    updated     : str = ""
    etat        : str = ""
    note        : float = 0
    sortie      : str = ""
    priorite    : int = 0
    nb_saison   : int = 0
    nb_ep_vu    : int = 0
    nb_ep_res   : int = 0
    nb_ep_tot   : int = 0
    nb_vu       : int = 0
    s1_vu       : int = 0
    s1_tot      : int = 0
    s2_vu       : int = 0
    s2_tot      : int = 0
    s3_vu       : int = 0
    s3_tot      : int = 0
    s4_vu       : int = 0
    s4_tot      : int = 0
    s5_vu       : int = 0
    s5_tot      : int = 0
    s6_vu       : int = 0
    s6_tot      : int = 0
    s7_vu       : int = 0
    s7_tot      : int = 0
    s8_vu       : int = 0
    s8_tot      : int = 0
    notice    : str = ""