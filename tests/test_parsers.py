from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

from models import Row
from parsers import (
    is_any_none, none_if_empty, parse_checkbox_or_none,
    parse_time_or_none, should_write_off,
)


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        ("TRUE", True),
        ("FALSE", False),
        ("true", None),
        ("false", None),
        ("other", None),
        ("", None),
        (None, None),
    ]
)
def test_parse_checkbox_or_none(input_value, expected_output):
    assert parse_checkbox_or_none(input_value) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        ("hello", "hello"),
        ([1, 2, 3], [1, 2, 3]),
        ({1: "a", 2: "b"}, {1: "a", 2: "b"}),
        ("", None),
        ([], None),
        ({}, None),
        (set(), None),
        (None, None),
    ],
)
def test_none_if_empty(input_value, expected_output):
    assert none_if_empty(input_value) == expected_output


@pytest.mark.parametrize(
    "time_str, expected_time",
    [
        ("10:30:00", time(10, 30, 0)),
        ("18:45:25", time(18, 45, 25)),
        ("09:00", time(9, 0, 0)),
        ("23:59", time(23, 59, 0)),
    ],
)
def test_parse_time_or_none_valid(time_str, expected_time):
    timezone = ZoneInfo('UTC')
    actual = parse_time_or_none(time_str, timezone)
    expected = expected_time.replace(tzinfo=timezone)
    assert actual == expected


@pytest.mark.parametrize(
    "invalid_time_str",
    [
        "25:00:00",  # Invalid hour
        "12:60:00",  # Invalid minute
        "10:30:65",  # Invalid second
        "invalid",  # Completely invalid format
        "10:30:00:00",  # Too many parts
    ]
)
def test_parse_time_or_none_invalid(invalid_time_str):
    timezone = ZoneInfo('UTC')
    assert parse_time_or_none(invalid_time_str, timezone) is None


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ((1, 2, 3), False),
        ((None, 2, 3), True),
        ((1, None, 3), True),
        ((1, 2, None), True),
        ((None, None, None), True),
        ([], False),
    ],
)
def test_is_any_none(args, expected_result):
    assert is_any_none(*args) == expected_result


@pytest.mark.parametrize(
    "row_time, expected_result",
    [
        (time(hour=10, second=0), True),
        (time(hour=10, second=1), False),
        (time(hour=9, minute=59, second=0), True),
        (time(hour=9, minute=58, second=59), False),
        (time(hour=10, minute=1), False),
        (time(hour=10, second=59), False),
    ],
)
def test_should_write_off(row_time, expected_result):
    now = datetime(2023, 11, 7, 10)
    row = Row(
        ingredient_name='test',
        to_write_off_at=row_time,
        is_written_off=False,
    )
    assert should_write_off(row, now) == expected_result
