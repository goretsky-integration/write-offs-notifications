import datetime
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel

__all__ = ('Worksheet', 'Row', 'Unit')


@dataclass(frozen=True, slots=True)
class Row:
    ingredient_name: str
    to_write_off_at: datetime.time
    is_written_off: bool


@dataclass(frozen=True, slots=True)
class Worksheet:
    title: str
    rows: list[Row]


class Unit(BaseModel):
    id: int
    name: str
    uuid: UUID
