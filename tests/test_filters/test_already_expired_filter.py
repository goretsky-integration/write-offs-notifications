import datetime

import pytest

from filters import AlreadyExpiredFilter


@pytest.fixture
def now() -> datetime.datetime:
    return datetime.datetime(2024, 6, 15, 12)


@pytest.fixture
def already_expired_filter() -> AlreadyExpiredFilter:
    return AlreadyExpiredFilter(interval_in_seconds=600)


@pytest.mark.parametrize(
    'time',
    [
        datetime.time(11, 30, 0),
        datetime.time(11, 40, 0),
        datetime.time(11, 40, 30),
        datetime.time(11, 50, 0),
        datetime.time(11, 50, 30),
        datetime.time(11, 50, 59),
        datetime.time(11, 51, 0),
        datetime.time(12, 0, 0),
        datetime.time(12, 0, 30),
        datetime.time(12, 0, 59),
        datetime.time(12, 1, 0),
    ],
)
def test_already_expired_filter_satisfied(
        time: datetime.time,
        now: datetime.datetime,
        already_expired_filter: AlreadyExpiredFilter,
):
    assert already_expired_filter(now, time)


@pytest.mark.parametrize(
    'time',
    [
        datetime.time(11, 49, 59),
        datetime.time(11, 39, 1),
        datetime.time(11, 51, 1),
        datetime.time(11, 59, 59),
        datetime.time(12, 10, 0),
        datetime.time(12, 10, 30),
    ],
)
def test_already_expired_filter_unsatisfied(
        time: datetime.time,
        now: datetime.datetime,
        already_expired_filter: AlreadyExpiredFilter
):
    assert not already_expired_filter(now, time)


if __name__ == '__main__':
    pytest.main()
