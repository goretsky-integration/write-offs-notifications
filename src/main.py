import datetime
import pathlib

import gspread

from config import load_config
from google_sheets import SpreadsheetContext
from parsers import (
    filter_worksheet_upcoming_write_offs,
    parse_worksheets_values,
)
from units_storage import get_units


def main() -> None:
    config_file_path = pathlib.Path(__file__).parent.parent / 'config.toml'
    config = load_config(config_file_path)

    now = datetime.datetime.now(config.timezone)

    units = get_units(base_url=config.units_storage_base_url)

    client = gspread.service_account(config.google_sheets_credentials_file_path)
    spreadsheet = client.open_by_key(config.spreadsheet_key)

    spreadsheet_context = SpreadsheetContext(
        spreadsheet=spreadsheet,
        titles_whitelist={unit.name for unit in units}
    )
    value_ranges = spreadsheet_context.get_values(now)

    worksheets = parse_worksheets_values(value_ranges, config.timezone)

    worksheets_with_upcoming_write_offs = [
        filter_worksheet_upcoming_write_offs(worksheet, now)
        for worksheet in worksheets
    ]

    print(worksheets_with_upcoming_write_offs)


if __name__ == '__main__':
    main()
