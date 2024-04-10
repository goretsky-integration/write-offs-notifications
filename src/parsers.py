import collections
import datetime
from collections.abc import Iterable, Mapping, Sized
from dataclasses import dataclass
from typing import TypeVar
from zoneinfo import ZoneInfo

from filters import AlreadyExpiredFilter, BeforeExpiredFilter
from models import Event, EventPayload, Row, Worksheet

__all__ = (
    'parse_checkbox_or_none',
    'parse_time_or_none',
    'is_any_none',
    'none_if_empty',
    'serialize_upcoming_write_offs',
    'parse_worksheets_values',
)

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
    ingredient_name_column: list[str] | None = None
    to_write_off_at_column: list[str] | None = None
    is_written_off_column: list[str] | None = None

    def build(self, timezone: ZoneInfo) -> Worksheet:
        zipped = zip(
            self.ingredient_name_column,
            self.to_write_off_at_column,
            self.is_written_off_column,
        )

        rows: list[Row] = []

        for ingredient_name, to_write_off_at, is_written_off in zipped:
            ingredient_name = none_if_empty(ingredient_name)
            to_write_off_at = parse_time_or_none(to_write_off_at, timezone)
            is_written_off = parse_checkbox_or_none(is_written_off)

            if is_any_none(
                    ingredient_name,
                    to_write_off_at,
                    is_written_off,
            ):
                continue

            row = Row(
                ingredient_name=ingredient_name,
                to_write_off_at=to_write_off_at,
                is_written_off=is_written_off,
            )
            rows.append(row)

        return Worksheet(title=self.title, rows=rows)


def parse_worksheets_values(
        value_ranges: Iterable[Mapping],
        timezone: ZoneInfo,
) -> list[Worksheet]:
    title_to_builders = collections.defaultdict(WorksheetRowsBuilder)

    for value_range in value_ranges:
        value_range: dict

        title, values_range = value_range['range'].split('!')
        values_range: str

        title = title.strip("'")

        builder = title_to_builders[title]

        if values_range.startswith('A'):
            builder.title = title
            builder.ingredient_name_column = value_range['values'][0]
        else:
            builder.to_write_off_at_column = value_range['values'][0]
            builder.is_written_off_column = value_range['values'][1]

    return [builder.build(timezone) for builder in title_to_builders.values()]


def check_upcoming_write_off(
        now: datetime.datetime,
        expires_at: datetime.time,
) -> str | None:
    filters = (
        AlreadyExpiredFilter(interval_in_seconds=600),
        BeforeExpiredFilter(
            event_type='EXPIRE_AT_15_MINUTES',
            fire_before_in_seconds=900,
        ),
        BeforeExpiredFilter(
            event_type='EXPIRE_AT_10_MINUTES',
            fire_before_in_seconds=600,
        ),
        BeforeExpiredFilter(
            event_type='EXPIRE_AT_5_MINUTES',
            fire_before_in_seconds=300,
        ),
    )

    for write_offs_filter in filters:
        if write_offs_filter(now=now, expires_at=expires_at):
            return write_offs_filter.event_type


def serialize_upcoming_write_offs(
        worksheets: Iterable[Worksheet],
        now: datetime.datetime,
        unit_name_to_id: Mapping[str, int],
) -> list[Event]:
    events = []

    for worksheet in worksheets:

        for row in worksheet.rows:

            if row.is_written_off:
                continue

            event_type = check_upcoming_write_off(
                now=now,
                expires_at=row.to_write_off_at,
            )
            if event_type is None:
                continue

            try:
                unit_id = unit_name_to_id[worksheet.title]
            except KeyError:
                continue

            event = Event(
                unit_ids=[unit_id],
                payload=EventPayload(
                    unit_name=worksheet.title,
                    ingredient_name=row.ingredient_name,
                    type=event_type,
                ),
            )
            events.append(event)

    return events
