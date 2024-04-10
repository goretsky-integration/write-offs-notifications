import collections
import datetime
from collections.abc import Iterable, Mapping, Sized
from dataclasses import dataclass
from typing import TypeVar
from zoneinfo import ZoneInfo

from models import Row, Worksheet

__all__ = (
    'parse_checkbox_or_none',
    'parse_time_or_none',
    'is_any_none',
    'none_if_empty',
    'should_write_off',
    'filter_worksheet_upcoming_write_offs',
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


def filter_not_written_off(rows: Iterable[Row]) -> list[Row]:
    return [row for row in rows if not row.is_written_off]


def should_write_off(
        row: Row,
        now: datetime.datetime,
) -> bool:
    to_write_off_at = datetime.datetime.combine(
        date=now.date(),
        time=row.to_write_off_at,
        tzinfo=now.tzinfo,
    )
    delta = now - to_write_off_at
    return 0 <= delta.total_seconds() <= 60


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


def filter_worksheet_upcoming_write_offs(
        worksheet: Worksheet,
        now: datetime.datetime,
) -> Worksheet:
    return Worksheet(
        title=worksheet.title,
        rows=[row for row in worksheet.rows if should_write_off(row, now)]
    )
