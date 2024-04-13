import datetime
from dataclasses import dataclass

from enums import WriteOffType

__all__ = ('BeforeExpiredFilter', 'AlreadyExpiredFilter', 'time_to_datetime')


def time_to_datetime(
        time: datetime.time,
        now: datetime.datetime,
) -> datetime.datetime:
    return datetime.datetime.combine(
        date=now.date(),
        time=time,
        tzinfo=now.tzinfo,
    )


@dataclass(frozen=True, slots=True)
class BeforeExpiredFilter:
    event_type: WriteOffType
    fire_before_in_seconds: int

    def __call__(
            self,
            now: datetime.datetime,
            expires_at: datetime.time,
    ) -> bool:
        expires_at = time_to_datetime(expires_at, now)
        diff = (expires_at - now).total_seconds()
        start = self.fire_before_in_seconds - 60
        end = self.fire_before_in_seconds
        return start <= diff <= end


@dataclass(frozen=True, slots=True)
class AlreadyExpiredFilter:
    interval_in_seconds: int
    event_type: str = WriteOffType.ALREADY_EXPIRED

    def __call__(
            self,
            now: datetime.datetime,
            expires_at: datetime.time,
    ) -> bool:
        expires_at = time_to_datetime(expires_at, now)
        diff = (now - expires_at).total_seconds() + 60

        if diff < 0:
            return False

        return 0 <= diff % self.interval_in_seconds <= 60
