from typing import Optional
from py_dto import DTO

class ScheduleCommand(DTO):
    query: str

class SearchCommand(DTO):
    query: str
    fromDate: Optional[int]
    toDate: Optional[int]

class TokenCommand(DTO):
    token: str
