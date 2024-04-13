import datetime
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from enums import WriteOffType

__all__ = (
    'Worksheet',
    'Row',
    'Unit',
    'NotificationEvent',
    'EventPayload',
    'RGBColor',
    'WriteOffWorksheetCoordinates',
    'ScheduledWriteOff',
)


class WriteOffWorksheetCoordinates(BaseModel):
    unit_name: str
    row_number: int
    write_off_time_column_number: int
    checkbox_column_number: int


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
    write_off_time_a1_coordinates: str
    checkbox_a1_coordinates: str


class NotificationEvent(BaseModel):
    """Event that will be to the notifications router service."""
    unit_ids: list[int]
    payload: EventPayload
    type: str = Field(default='WRITE_OFFS', frozen=True)


class RGBColor(BaseModel):
    red: Annotated[float, Field(ge=0, le=1)]
    green: Annotated[float, Field(ge=0, le=1)]
    blue: Annotated[float, Field(ge=0, le=1)]
