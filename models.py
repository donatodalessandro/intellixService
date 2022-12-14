from typing import Optional
from py_dto import DTO

class ScheduleCommand(DTO):
    query: str


class SearchCommand(DTO):
    query: str
    fromDate: Optional[int]
    toDate: Optional[int]

class ResultIntelix(DTO):
    id: str
    name: str
    date: int
    typeh: str
    bucket: str


class SearchResult:
    id: str
    name: str
    date: int
    typeh: str
    bucket: str


class SeachScheduleResponse:
    id: str
    timestamp: int
    query: str
    result: list[SearchResult]
