import asyncio
import datetime
import pathlib

import gspread

from config import load_config
from google_sheets import SpreadsheetContext
from message_queue import publish_events
from parsers import parse_worksheets_values, serialize_upcoming_write_offs
from units_storage import get_units


async def main() -> None:
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

    events = serialize_upcoming_write_offs(
        worksheets=worksheets,
        now=now,
        unit_name_to_id={unit.name: unit.id for unit in units},
    )

    await publish_events(
        message_queue_url=config.message_queue_url,
        events=events
    )


if __name__ == '__main__':
    asyncio.run(main())
