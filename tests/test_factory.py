import pytest

import depcalc.factory as f
from depcalc.lazy import (
    LazyRequirement,
    RawLazyReleaseSet,
    get_lazy_specifier,
    get_marker,
)
from depcalc.versiontoken import VersionToken


def test_version() -> None:
    assert isinstance(f.version, VersionToken)
    assert isinstance(f.v, VersionToken)


@pytest.mark.parametrize(
    "requirement,expected",
    [
        (
            f.package("depcalc"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.pkg("depcalc"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.url("http://path/v1.2.3"),
            LazyRequirement(
                package=None,
                url="http://path/v1.2.3",
                extras=set(),
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.extra("extra"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra"},
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.specifier(">=1.2.3"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier={get_lazy_specifier(">=1.2.3")},
                marker=None,
            ),
        ),
        (
            f.marker("python_version=='1.2.3'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=set(),
                marker=get_marker("python_version=='1.2.3'"),
            ),
        ),
    ],
)
def test_factories(requirement: LazyRequirement, expected: LazyRequirement) -> None:
    assert requirement == expected


def test_releases() -> None:
    assert RawLazyReleaseSet(None) == f.releases()
    assert RawLazyReleaseSet("depcalc") == f.releases("depcalc")
