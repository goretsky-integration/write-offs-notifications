import pathlib
import tomllib
from dataclasses import dataclass
from zoneinfo import ZoneInfo

__all__ = ('Config', 'load_config',)


@dataclass(frozen=True, slots=True)
class Config:
    google_sheets_credentials_file_path: pathlib.Path
    spreadsheet_key: str
    timezone: ZoneInfo
    units_storage_base_url: str
    message_queue_url: str


def load_config(file_path: pathlib.Path) -> Config:
    config_text = file_path.read_text(encoding='utf-8')
    config = tomllib.loads(config_text)

    google_sheets_credentials_file_path = (
        pathlib.Path(config['google_sheets']['credentials_file_path'])
    )
    spreadsheet_key = config['google_sheets']['spreadsheet_key']
    timezone = ZoneInfo(config['timezone'])
    units_storage_base_url = config['units_storage']['base_url']
    message_queue_url = config['message_queue']['url']

    return Config(
        google_sheets_credentials_file_path=google_sheets_credentials_file_path,
        spreadsheet_key=spreadsheet_key,
        timezone=timezone,
        units_storage_base_url=units_storage_base_url,
        message_queue_url=message_queue_url,
    )
