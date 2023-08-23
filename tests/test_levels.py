import pytest
from packaging.version import Version

from compreq import AnyLevel, IntLevel, Level, RelativeToFirstNonZeroLevel, get_level


@pytest.mark.parametrize(
    "level,version,expected",
    [
        (IntLevel(0), Version("1.2.3"), 0),
        (IntLevel(1), Version("1.2.3"), 1),
        (IntLevel(-1), Version("1.2.3"), -1),
        (RelativeToFirstNonZeroLevel(0), Version("1.2.3"), 0),
        (RelativeToFirstNonZeroLevel(1), Version("1.2.3"), 1),
        (RelativeToFirstNonZeroLevel(0), Version("0.1.0"), 1),
        (RelativeToFirstNonZeroLevel(1), Version("0.1.0"), 2),
    ],
)
def test_level__index(level: Level, version: Version, expected: int) -> None:
    assert expected == level.index(version)


@pytest.mark.parametrize(
    "level,expected",
    [
        (3, IntLevel(3)),
        (IntLevel(4), IntLevel(4)),
    ],
)
def test_get_level(level: AnyLevel, expected: Level) -> None:
    assert expected == get_level(level)
