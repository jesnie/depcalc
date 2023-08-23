import datetime as dt
from typing import Any

import pytest

from compreq import is_utc_datetime, utc_now


@pytest.mark.parametrize(
    "time,expected",
    [
        (None, False),
        ("2023-15-11", False),
        (dt.datetime(2023, 8, 17, 15, 12), False),
        (dt.datetime(2023, 8, 17, 15, 12, tzinfo=dt.timezone.utc), True),
    ],
)
def test_is_utc_datetime(time: Any, expected: bool) -> None:
    assert expected == is_utc_datetime(time)


def test_utc_now() -> None:
    assert is_utc_datetime(utc_now())
