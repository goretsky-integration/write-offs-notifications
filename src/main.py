import asyncio
import datetime
import logging
import pathlib

import gspread

from colors import WRITE_OFF_TYPE_TO_COLOR
from config import load_config
from google_sheets import SpreadsheetContext, WorksheetContext
from message_queue import publish_events
from parsers import parse_worksheets_values, serialize_upcoming_write_offs
from units_storage import get_units

logger = logging.getLogger(__name__)


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

    write_offs = parse_worksheets_values(value_ranges, config.timezone)

    events = serialize_upcoming_write_offs(
        write_offs=write_offs,
        now=now,
        unit_name_to_id={unit.name: unit.id for unit in units},
    )

    if not events:
        logger.info('No events')
        return

    await publish_events(
        message_queue_url=config.message_queue_url,
        events=events
    )

    for event in events:
        worksheet = spreadsheet_context.get_worksheet_by_title(
            title=event.payload.unit_name,
        )
        background_color = WRITE_OFF_TYPE_TO_COLOR[event.payload.type]
        worksheet_context = WorksheetContext(worksheet)

        worksheet_context.update_cell_color(
            cell_coordinates=event.payload.write_off_time_a1_coordinates,
            background_color=background_color,
        )


if __name__ == '__main__':
    asyncio.run(main())
