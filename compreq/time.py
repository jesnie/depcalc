import datetime as dt
from typing import Any, NewType, TypeGuard

UtcDatetime = NewType("UtcDatetime", dt.datetime)


def is_utc_datetime(time: Any) -> TypeGuard[UtcDatetime]:
    if type(time) != dt.datetime:  # pylint: disable=unidiomatic-typecheck
        return False
    if time.tzinfo is not None:
        return time.tzinfo.tzname(None) == "UTC"
    return False


def utc_now() -> UtcDatetime:
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    assert is_utc_datetime(now)
    return now
