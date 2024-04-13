import datetime
import string
from functools import cache
from typing import Iterable

from gspread import Spreadsheet, Worksheet
from gspread.utils import Dimension

from models import RGBColor

__all__ = ('compute_ranges', 'SpreadsheetContext', 'compute_worksheet_ranges')


def compute_values_column_letters(
        weekday: int,
) -> tuple[str, str]:
    to_write_off_at_column = string.ascii_uppercase[weekday * 2 - 1]
    is_written_off_column = string.ascii_uppercase[weekday * 2]
    return to_write_off_at_column, is_written_off_column


def compute_worksheet_ranges(
        worksheet_title: str,
        to_write_off_at_column: str,
        is_written_off_column: str
) -> tuple[str, str]:
    return (
        f'{worksheet_title}!A2:A',
        f'{worksheet_title}!{to_write_off_at_column}2:{is_written_off_column}',
    )


def compute_ranges(
        *,
        worksheet_titles: Iterable[str],
        now: datetime.datetime
) -> list[str]:
    to_write_off_at_column, is_written_off_column = (
        compute_values_column_letters(now.isoweekday())
    )
    ranges = []
    for title in worksheet_titles:
        ranges += compute_worksheet_ranges(
            worksheet_title=title,
            to_write_off_at_column=to_write_off_at_column,
            is_written_off_column=is_written_off_column,
        )
    return ranges


class SpreadsheetContext:

    def __init__(
            self,
            *,
            spreadsheet: Spreadsheet,
            titles_whitelist: Iterable[str],
    ):
        self.__spreadsheet = spreadsheet
        self.__titles_whitelist = set(titles_whitelist)

    @cache
    def get_worksheets(self) -> list[Worksheet]:
        return self.__spreadsheet.worksheets(exclude_hidden=True)

    def get_titles(self) -> set[str]:
        return {
            worksheet.title for worksheet in self.get_worksheets()
            if worksheet.title in self.__titles_whitelist
        }

    @cache
    def get_worksheet_by_title(self, title: str) -> Worksheet | None:
        worksheets = self.get_worksheets()
        for worksheet in worksheets:
            if worksheet.title == title:
                return worksheet

    def get_values(self, now: datetime.datetime) -> list[dict]:
        worksheet_titles = self.get_titles()
        ranges = compute_ranges(worksheet_titles=worksheet_titles, now=now)

        values_response = self.__spreadsheet.values_batch_get(
            ranges=ranges,
            params={'majorDimension': Dimension.cols}
        )
        return values_response['valueRanges']


class WorksheetContext:

    def __init__(self, worksheet: Worksheet):
        self.__worksheet = worksheet

    def update_cell_color(
            self,
            *,
            cell_coordinates: str,
            background_color: RGBColor,
    ):
        self.__worksheet.format(cell_coordinates, {
            "backgroundColor": {
                "red": background_color.red,
                "green": background_color.green,
                "blue": background_color.blue,
            },
        })
