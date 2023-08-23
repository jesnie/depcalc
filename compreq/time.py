import datetime as dt
from typing import Any, NewType, TypeGuard

UtcDatetime = NewType("UtcDatetime", dt.datetime)


def is_utc_datetime(time: Any) -> TypeGuard[UtcDatetime]:
    """
    Check whether this object is a `UtcDatetime`.

    You can use this to cast an object to a `UtcDatetime` with a simple assert::

        from compreq import is_utc_datetime
        import datetime as dt

        t = dt.datetime.now()
        reveal_type(t)  # note: Revealed type is "datetime.datetime"
        assert is_utc_datetime(t)
        reveal_type(t)  # note: Revealed type is "compreq.time.UtcDatetime"
    """
    if type(time) != dt.datetime:  # pylint: disable=unidiomatic-typecheck
        return False
    if time.tzinfo is not None:
        return time.tzinfo.tzname(None) == "UTC"
    return False


def utc_now() -> UtcDatetime:
    """Get the current time as a `UtcDatetime`."""
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    assert is_utc_datetime(now)
    return now
