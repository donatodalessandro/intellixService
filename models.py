from typing import Optional
from py_dto import DTO

class ScheduleCommand(DTO):

    """
       Comando per veicolare la query su cui istanziare lo scheduler
    """
    query: str

class SearchCommand(DTO):
    """
       Comando per veicolare la query e eventuali date di inizio e di fine
    """
    query: str
    fromDate: Optional[int]
    toDate: Optional[int]

class TokenCommand(DTO):
    """
       Comando per veicolare il token per abilitare la ricerca su intelx
    """
    token: str
