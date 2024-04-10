import datetime

import pytest

from filters import BeforeExpiredFilter


@pytest.mark.parametrize(
    'time, fire_before_in_seconds, expected',
    [
        (datetime.time(12, 15, 1), 900, False),
        (datetime.time(12, 15, 0), 900, True),
        (datetime.time(12, 14, 0), 900, True),
        (datetime.time(12, 14, 1), 900, True),
        (datetime.time(12, 13, 59), 900, False),
    ]
)
def test_before_expired_filter(
        time: datetime.time,
        fire_before_in_seconds: int,
        expected: bool,
):
    now = datetime.datetime(2024, 6, 15, 12)
    before_expired_filter = BeforeExpiredFilter(
        event_type='EXPIRE_AT_15_MINUTES',
        fire_before_in_seconds=fire_before_in_seconds,
    )
    assert before_expired_filter(now, time) == expected
