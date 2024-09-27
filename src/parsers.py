import collections
import datetime
import itertools
import logging
from collections.abc import Generator, Iterable, Mapping, Sized
from dataclasses import dataclass
from typing import Protocol, TypeVar
from zoneinfo import ZoneInfo

from gspread.utils import a1_range_to_grid_range, rowcol_to_a1

from enums import WriteOffType
from filters import AlreadyExpiredFilter, BeforeExpiredFilter
from models import (
    EventPayload, NotificationEvent, ScheduledWriteOff, Worksheet,
    WriteOffWorksheetCoordinates,
)

__all__ = (
    'parse_checkbox_or_none',
    'parse_time_or_none',
    'is_any_none',
    'none_if_empty',
    'serialize_upcoming_write_offs',
    'parse_worksheets_values',
)

logger = logging.getLogger('parser')

T = TypeVar('T', bound=Sized)


def none_if_empty(value: T) -> T | None:
    return value if value else None


def parse_checkbox_or_none(value: str) -> bool | None:
    """
    Checkboxes are represented as strings 'TRUE' and 'FALSE' in Google Sheets.
    """
    if value == 'TRUE':
        return True
    elif value == 'FALSE':
        return False


def parse_time_or_none(time: str, timezone: ZoneInfo) -> datetime.time | None:
    """Parse HH:MM:SS or HH:MM strings"""
    parts = time.split(':')

    if len(parts) == 3:
        hour, minutes, seconds = parts
    elif len(parts) == 2:
        hour, minutes = parts
        seconds = 0
    else:
        return

    try:
        hour = int(hour)
        minutes = int(minutes)
        seconds = int(seconds)
    except ValueError:
        return

    try:
        return datetime.time(
            hour=hour,
            minute=minutes,
            second=seconds,
            tzinfo=timezone,
        )
    except ValueError:
        return


def is_any_none(*args) -> bool:
    return any(arg is None for arg in args)


@dataclass(slots=True)
class WorksheetRowsBuilder:
    title: str | None = None
    write_off_time_column_number: int | None = None
    checkbox_column_number: int | None = None

    ingredient_name_column: list[str] | None = None
    to_write_off_at_column: list[str] | None = None
    is_written_off_column: list[str] | None = None

    def get_worksheet_coordinates(
            self,
            row_number: int,
    ) -> WriteOffWorksheetCoordinates:
        return WriteOffWorksheetCoordinates(
            unit_name=self.title,
            row_number=row_number,
            write_off_time_column_number=self.write_off_time_column_number,
            checkbox_column_number=self.checkbox_column_number,
        )

    def build(self, timezone: ZoneInfo) -> list[ScheduledWriteOff]:
        if is_any_none(
                self.ingredient_name_column,
                self.to_write_off_at_column,
                self.is_written_off_column,
        ):
            return []

        zipped = zip(
            self.ingredient_name_column,
            self.to_write_off_at_column,
            self.is_written_off_column,
        )

        write_offs: list[ScheduledWriteOff] = []

        for row_number, values in enumerate(zipped, start=2):
            ingredient_name, to_write_off_at, is_written_off = values

            ingredient_name = none_if_empty(ingredient_name)
            to_write_off_at = parse_time_or_none(to_write_off_at, timezone)
            is_written_off = parse_checkbox_or_none(is_written_off)

            if is_any_none(
                    ingredient_name,
                    to_write_off_at,
                    is_written_off,
            ):
                continue

            worksheet_coordinates = self.get_worksheet_coordinates(row_number)
            write_off = ScheduledWriteOff(
                ingredient_name=ingredient_name,
                to_write_off_at=to_write_off_at,
                is_written_off=is_written_off,
                worksheet_coordinates=worksheet_coordinates,
            )
            write_offs.append(write_off)

        return write_offs


def parse_worksheets_values(
        value_ranges: Iterable[Mapping],
        timezone: ZoneInfo,
) -> itertools.chain[Worksheet]:
    title_to_builders = collections.defaultdict(WorksheetRowsBuilder)

    for value_range in value_ranges:
        value_range: dict

        title, values_range = value_range['range'].split('!')
        values_range: str

        title = title.strip("'")

        builder = title_to_builders[title]

        is_ingredient_names_column = values_range.startswith('A')

        columns = value_range.get('values', [])

        if is_ingredient_names_column and len(columns) == 1:
            builder.title = title
            builder.ingredient_name_column = columns[0]
        elif not is_ingredient_names_column and len(columns) == 2:
            builder.to_write_off_at_column = columns[0]
            builder.is_written_off_column = columns[1]

            grid_range = a1_range_to_grid_range(values_range)
            write_off_time_column_number = grid_range['startColumnIndex'] + 1
            checkbox_column_number = grid_range['endColumnIndex']

            builder.write_off_time_column_number = write_off_time_column_number
            builder.checkbox_column_number = checkbox_column_number

    nested_write_offs = (
        builder.build(timezone)
        for builder in title_to_builders.values()
    )
    return itertools.chain.from_iterable(nested_write_offs)


def check_upcoming_write_off(
        now: datetime.datetime,
        expires_at: datetime.time,
) -> WriteOffType | None:
    filters = (
        AlreadyExpiredFilter(interval_in_seconds=600),
        BeforeExpiredFilter(
            event_type=WriteOffType.EXPIRE_AT_15_MINUTES,
            fire_before_in_seconds=900,
        ),
        BeforeExpiredFilter(
            event_type=WriteOffType.EXPIRE_AT_10_MINUTES,
            fire_before_in_seconds=600,
        ),
        BeforeExpiredFilter(
            event_type=WriteOffType.EXPIRE_AT_5_MINUTES,
            fire_before_in_seconds=300,
        ),
    )

    for write_offs_filter in filters:
        if write_offs_filter(now=now, expires_at=expires_at):
            return write_offs_filter.event_type


class HasIsWrittenOff(Protocol):
    is_written_off: bool


HasIsWrittenOffT = TypeVar('HasIsWrittenOffT', bound=HasIsWrittenOff)


def filter_written_off(
        items: Iterable[HasIsWrittenOffT],
) -> Generator[HasIsWrittenOffT, None, None]:
    return (item for item in items if not item.is_written_off)


def serialize_upcoming_write_offs(
        write_offs: Iterable[ScheduledWriteOff],
        now: datetime.datetime,
        unit_name_to_id: Mapping[str, int],
) -> list[NotificationEvent]:
    events: list[NotificationEvent] = []
    for write_off in filter_written_off(write_offs):

        event_type = check_upcoming_write_off(
            now=now,
            expires_at=write_off.to_write_off_at,
        )
        if event_type is None:
            continue

        unit_name = write_off.worksheet_coordinates.unit_name
        try:
            unit_id = unit_name_to_id[unit_name]
        except KeyError:
            logger.warning(f'Unit {unit_name} not found')
            continue

        write_off_time_a1_coordinates = rowcol_to_a1(
            row=write_off.worksheet_coordinates.row_number,
            col=write_off.worksheet_coordinates.write_off_time_column_number,
        )
        checkbox_a1_coordinates = rowcol_to_a1(
            row=write_off.worksheet_coordinates.row_number,
            col=write_off.worksheet_coordinates.checkbox_column_number,
        )

        payload = EventPayload(
            unit_name=unit_name,
            ingredient_name=write_off.ingredient_name,
            type=event_type,
            write_off_time_a1_coordinates=write_off_time_a1_coordinates,
            checkbox_a1_coordinates=checkbox_a1_coordinates,
        )
        event = NotificationEvent(unit_ids=[unit_id], payload=payload)
        logger.info(f'New event: {event}')
        events.append(event)

    return events
