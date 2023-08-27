import pytest
from packaging.version import Version

import compreq as cr


@pytest.mark.parametrize(
    "level,version,keep_trailing_zeros,expected",
    [
        (cr.REL_MAJOR, "1.2.3a4dev5", True, "2.0.0"),
        (cr.MICRO, "1.2.3a4dev5", True, "1.2.4"),
        (cr.MINOR, "1.2.3a4dev5", True, "1.3.0"),
        (cr.MAJOR, "1.2.3a4dev5", True, "2.0.0"),
        (cr.REL_MAJOR, "0.1.0", True, "0.2.0"),
        (cr.MICRO, "0.1.0", True, "0.1.1"),
        (cr.MINOR, "0.1.0", True, "0.2.0"),
        (cr.MAJOR, "0.1.0", True, "1.0.0"),
        (cr.REL_MAJOR, "1!1.2.3a4dev5", True, "1!2.0.0"),
        (cr.MICRO, "1!1.2.3a4dev5", True, "1!1.2.4"),
        (cr.MINOR, "1!1.2.3a4dev5", True, "1!1.3.0"),
        (cr.MAJOR, "1!1.2.3a4dev5", True, "1!2.0.0"),
        (cr.REL_MAJOR, "1!0.1.0", True, "1!0.2.0"),
        (cr.MICRO, "1!0.1.0", True, "1!0.1.1"),
        (cr.MINOR, "1!0.1.0", True, "1!0.2.0"),
        (cr.MAJOR, "1!0.1.0", True, "1!1.0.0"),
        (cr.REL_MAJOR, "1.2.3a4dev5", False, "2"),
        (cr.MICRO, "1.2.3a4dev5", False, "1.2.4"),
        (cr.MINOR, "1.2.3a4dev5", False, "1.3"),
        (cr.MAJOR, "1.2.3a4dev5", False, "2"),
        (cr.REL_MAJOR, "0.1.0", False, "0.2"),
        (cr.MICRO, "0.1.0", False, "0.1.1"),
        (cr.MINOR, "0.1.0", False, "0.2"),
        (cr.MAJOR, "0.1.0", False, "1"),
        (cr.REL_MAJOR, "1!1.2.3a4dev5", False, "1!2"),
        (cr.MICRO, "1!1.2.3a4dev5", False, "1!1.2.4"),
        (cr.MINOR, "1!1.2.3a4dev5", False, "1!1.3"),
        (cr.MAJOR, "1!1.2.3a4dev5", False, "1!2"),
        (cr.REL_MAJOR, "1!0.1.0", False, "1!0.2"),
        (cr.MICRO, "1!0.1.0", False, "1!0.1.1"),
        (cr.MINOR, "1!0.1.0", False, "1!0.2"),
        (cr.MAJOR, "1!0.1.0", False, "1!1"),
    ],
)
def test_ceil(level: cr.Level, version: str, keep_trailing_zeros: bool, expected: str) -> None:
    assert Version(expected) == cr.ceil(level, Version(version), keep_trailing_zeros)


@pytest.mark.parametrize(
    "level,version,keep_trailing_zeros,expected",
    [
        (cr.REL_MAJOR, "1.2.3a4dev5", True, "1.0.0"),
        (cr.MICRO, "1.2.3a4dev5", True, "1.2.3"),
        (cr.MINOR, "1.2.3a4dev5", True, "1.2.0"),
        (cr.MAJOR, "1.2.3a4dev5", True, "1.0.0"),
        (cr.REL_MAJOR, "0.1.0", True, "0.1.0"),
        (cr.MICRO, "0.1.0", True, "0.1.0"),
        (cr.MINOR, "0.1.0", True, "0.1.0"),
        (cr.MAJOR, "0.1.0", True, "0.0.0"),
        (cr.REL_MAJOR, "1!1.2.3a4dev5", True, "1!1.0.0"),
        (cr.MICRO, "1!1.2.3a4dev5", True, "1!1.2.3"),
        (cr.MINOR, "1!1.2.3a4dev5", True, "1!1.2.0"),
        (cr.MAJOR, "1!1.2.3a4dev5", True, "1!1.0.0"),
        (cr.REL_MAJOR, "1!0.1.0", True, "1!0.1.0"),
        (cr.MICRO, "1!0.1.0", True, "1!0.1.0"),
        (cr.MINOR, "1!0.1.0", True, "1!0.1.0"),
        (cr.MAJOR, "1!0.1.0", True, "1!0.0.0"),
        (cr.REL_MAJOR, "1.2.3a4dev5", False, "1"),
        (cr.MICRO, "1.2.3a4dev5", False, "1.2.3"),
        (cr.MINOR, "1.2.3a4dev5", False, "1.2"),
        (cr.MAJOR, "1.2.3a4dev5", False, "1"),
        (cr.REL_MAJOR, "0.1.0", False, "0.1"),
        (cr.MICRO, "0.1.0", False, "0.1.0"),
        (cr.MINOR, "0.1.0", False, "0.1"),
        (cr.MAJOR, "0.1.0", False, "0"),
        (cr.REL_MAJOR, "1!1.2.3a4dev5", False, "1!1"),
        (cr.MICRO, "1!1.2.3a4dev5", False, "1!1.2.3"),
        (cr.MINOR, "1!1.2.3a4dev5", False, "1!1.2"),
        (cr.MAJOR, "1!1.2.3a4dev5", False, "1!1"),
        (cr.REL_MAJOR, "1!0.1.0", False, "1!0.1"),
        (cr.MICRO, "1!0.1.0", False, "1!0.1.0"),
        (cr.MINOR, "1!0.1.0", False, "1!0.1"),
        (cr.MAJOR, "1!0.1.0", False, "1!0"),
    ],
)
def test_floor(level: cr.Level, version: str, keep_trailing_zeros: bool, expected: str) -> None:
    assert Version(expected) == cr.floor(level, Version(version), keep_trailing_zeros)
