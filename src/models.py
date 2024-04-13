import datetime
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from enums import WriteOffType

__all__ = ('Worksheet', 'Row', 'Unit', 'Event', 'EventPayload', 'RGBColor',
           'WriteOffWorksheetCoordinates', 'ScheduledWriteOff')


class WriteOffWorksheetCoordinates(BaseModel):
    unit_name: str
    row_number: int
    to_write_off_at_column_number: int
    is_written_off_column_number: int


class ScheduledWriteOff(BaseModel):
    ingredient_name: str
    to_write_off_at: datetime.time
    is_written_off: bool
    worksheet_coordinates: WriteOffWorksheetCoordinates


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


class EventPayload(BaseModel):
    type: WriteOffType
    unit_name: str
    ingredient_name: str


class Event(BaseModel):
    unit_ids: list[int]
    payload: EventPayload
    type: str = Field(default='WRITE_OFFS', frozen=True)


class RGBColor(BaseModel):
    red: Annotated[float, Field(ge=0, le=1)]
    green: Annotated[float, Field(ge=0, le=1)]
    blue: Annotated[float, Field(ge=0, le=1)]
