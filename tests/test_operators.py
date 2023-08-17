import datetime as dt
from typing import Collection, Sequence
from unittest.mock import MagicMock

import pytest
from packaging.version import Version

import compreq.operators as o
from compreq.context import PackageContext
from compreq.lazy import (
    AllLazyReleaseSet,
    LazyRequirement,
    LazySpecifierSet,
    PreLazyReleaseSet,
    ProdLazyReleaseSet,
    get_lazy_specifier,
    get_lazy_specifier_set,
    get_marker,
)
from compreq.versiontoken import VersionToken
from tests.utils import fake_release, fake_release_set


def test_version() -> None:
    assert isinstance(o.version, VersionToken)
    assert isinstance(o.v, VersionToken)


@pytest.mark.parametrize(
    "requirement,expected",
    [
        (
            o.package("compreq"),
            LazyRequirement(
                package="compreq",
                url=None,
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            o.pkg("compreq"),
            LazyRequirement(
                package="compreq",
                url=None,
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            o.url("http://path/v1.2.3"),
            LazyRequirement(
                package=None,
                url="http://path/v1.2.3",
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            o.extra("extra"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra"},
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            o.specifier(">=1.2.3"),
            get_lazy_specifier(">=1.2.3"),
        ),
        (
            o.specifier_set(">=1.2.3,<2.0.0"),
            get_lazy_specifier_set(">=1.2.3,<2.0.0"),
        ),
        (
            o.marker("python_version=='1.2.3'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=get_marker("python_version=='1.2.3'"),
            ),
        ),
    ],
)
def test_factories(requirement: LazyRequirement, expected: LazyRequirement) -> None:
    assert requirement == expected


def test_releases() -> None:
    assert ProdLazyReleaseSet(AllLazyReleaseSet(None)) == o.releases()
    assert ProdLazyReleaseSet(AllLazyReleaseSet("compreq")) == o.releases("compreq")


def test_prereleases() -> None:
    assert PreLazyReleaseSet(AllLazyReleaseSet(None)) == o.prereleases()
    assert PreLazyReleaseSet(AllLazyReleaseSet("compreq")) == o.prereleases("compreq")


def test_devreleases() -> None:
    assert AllLazyReleaseSet(None) == o.devreleases()
    assert AllLazyReleaseSet("compreq") == o.devreleases("compreq")


@pytest.mark.parametrize(
    "releases,expected",
    [
        (["1!1.0.0", "1.2.3", "1.2.3a1", "1.2.3a1dev1", "1.2.2"], "1.2.2"),
        (["1!1.0.0", "1.2.3", "1.2.3a1", "1.2.3a1dev1"], "1.2.3a1dev1"),
        (["1!1.0.0", "1.2.3", "1.2.3a1"], "1.2.3a1"),
        (["1!1.0.0", "1.2.3"], "1.2.3"),
        (["1!1.0.0"], "1!1.0.0"),
    ],
)
def test_min_ver(releases: Collection[str], expected: str) -> None:
    release_set = fake_release_set(releases=releases, infer_successors=False)
    context = MagicMock(PackageContext)
    context.package = "compreq"
    min_ver = o.min_ver(release_set)
    assert fake_release(version=expected) == min_ver.resolve(context)
    assert context.releases.called_once_with("compreq")


@pytest.mark.parametrize(
    "releases,expected",
    [
        (["1!1.0.0", "1.2.3", "1.2.3a1", "1.2.3a1dev1", "1.2.2"], "1!1.0.0"),
        (["1.2.3", "1.2.3a1", "1.2.3a1dev1", "1.2.2"], "1.2.3"),
        (["1.2.3a1", "1.2.3a1dev1", "1.2.2"], "1.2.3a1"),
        (["1.2.3a1dev1", "1.2.2"], "1.2.3a1dev1"),
        (["1.2.2"], "1.2.2"),
    ],
)
def test_max_ver(releases: Collection[str], expected: str) -> None:
    release_set = fake_release_set(releases=releases, infer_successors=False)
    context = MagicMock(PackageContext)
    context.package = "compreq"
    max_ver = o.max_ver(release_set)
    assert fake_release(version=expected) == max_ver.resolve(context)
    assert context.releases.called_once_with("compreq")


@pytest.mark.parametrize(
    "versions,expected",
    [
        (["1.0.0", "1.1.0", "1.1.1"], "1.0.0"),
        (["1.1.0", "1.1.1"], "1.1.0"),
        (["1.1.1"], "1.1.1"),
    ],
)
def test_minimum_ver(versions: Sequence[str], expected: str) -> None:
    context = MagicMock(PackageContext)
    lazy = o.minimum_ver(*versions)
    assert Version(expected) == lazy.resolve(context)


@pytest.mark.parametrize(
    "versions,expected",
    [
        (["1.0.0", "1.1.0", "1.1.1"], "1.1.1"),
        (["1.0.0", "1.1.0"], "1.1.0"),
        (["1.0.0"], "1.0.0"),
    ],
)
def test_maximum_ver(versions: Sequence[str], expected: str) -> None:
    context = MagicMock(PackageContext)
    lazy = o.maximum_ver(*versions)
    assert Version(expected) == lazy.resolve(context)


@pytest.mark.parametrize(
    "level,version,expected",
    [
        (o.MICRO, "1.2.3a4dev5", "1.2.4"),
        (o.MINOR, "1.2.3a4dev5", "1.3.0"),
        (o.MAJOR, "1.2.3a4dev5", "2.0.0"),
        (o.MICRO, "1!1.2.3a4dev5", "1!1.2.4"),
        (o.MINOR, "1!1.2.3a4dev5", "1!1.3.0"),
        (o.MAJOR, "1!1.2.3a4dev5", "1!2.0.0"),
    ],
)
def test_ceil_ver(level: int, version: str, expected: str) -> None:
    context = MagicMock(PackageContext)
    ceil_ver = o.ceil_ver(level, version)
    assert Version(expected) == ceil_ver.resolve(context)


@pytest.mark.parametrize(
    "level,version,expected",
    [
        (o.MICRO, "1.2.3a4dev5", "1.2.3"),
        (o.MINOR, "1.2.3a4dev5", "1.2.0"),
        (o.MAJOR, "1.2.3a4dev5", "1.0.0"),
        (o.MICRO, "1!1.2.3a4dev5", "1!1.2.3"),
        (o.MINOR, "1!1.2.3a4dev5", "1!1.2.0"),
        (o.MAJOR, "1!1.2.3a4dev5", "1!1.0.0"),
    ],
)
def test_floor_ver(level: int, version: str, expected: str) -> None:
    context = MagicMock(PackageContext)
    floor_ver = o.floor_ver(level, version)
    assert Version(expected) == floor_ver.resolve(context)


def test_min_age() -> None:
    context = MagicMock(PackageContext)
    context.package = "compreq"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    min_age = o.min_age(
        release_set, now=dt.datetime(2023, 8, 16, 16, 5, 0), minutes=3, allow_empty=True
    )
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
        ],
        infer_successors=False,
    ) == min_age.resolve(context)


def test_min_age__empty_allowed() -> None:
    context = MagicMock(PackageContext)
    context.package = "compreq"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    min_age = o.min_age(
        release_set, now=dt.datetime(2023, 8, 16, 16, 5, 0), minutes=6, allow_empty=True
    )
    assert fake_release_set(
        releases=[],
        infer_successors=False,
    ) == min_age.resolve(context)


def test_min_age__empty_not_allowed() -> None:
    context = MagicMock(PackageContext)
    context.package = "compreq"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    min_age = o.min_age(
        release_set, now=dt.datetime(2023, 8, 16, 16, 5, 0), minutes=6, allow_empty=False
    )
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
        ],
        infer_successors=False,
    ) == min_age.resolve(context)


def test_max_age() -> None:
    context = MagicMock(PackageContext)
    context.package = "compreq"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    max_age = o.max_age(
        release_set, now=dt.datetime(2023, 8, 16, 16, 5, 0), minutes=3, allow_empty=True
    )
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    ) == max_age.resolve(context)


def test_max_age__empty_allowed() -> None:
    context = MagicMock(PackageContext)
    context.package = "compreq"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    max_age = o.max_age(
        release_set, now=dt.datetime(2023, 8, 16, 16, 10, 0), minutes=3, allow_empty=True
    )
    assert fake_release_set(
        releases=[],
        infer_successors=False,
    ) == max_age.resolve(context)


def test_max_age__empty_not_allowed() -> None:
    context = MagicMock(PackageContext)
    context.package = "compreq"
    release_set = fake_release_set(
        releases=[
            fake_release(version="1.0.0", released_time=dt.datetime(2023, 8, 16, 16, 0, 0)),
            fake_release(version="1.0.1", released_time=dt.datetime(2023, 8, 16, 16, 1, 0)),
            fake_release(version="1.0.2", released_time=dt.datetime(2023, 8, 16, 16, 2, 0)),
            fake_release(version="1.0.3", released_time=dt.datetime(2023, 8, 16, 16, 3, 0)),
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    )
    max_age = o.max_age(
        release_set, now=dt.datetime(2023, 8, 16, 16, 10, 0), minutes=3, allow_empty=False
    )
    assert fake_release_set(
        releases=[
            fake_release(version="1.0.4", released_time=dt.datetime(2023, 8, 16, 16, 4, 0)),
        ],
        infer_successors=False,
    ) == max_age.resolve(context)


@pytest.mark.parametrize(
    "level,n,releases,expected",
    [
        (
            o.MAJOR,
            3,
            [
                "1.0.0",
                "2.0.0",
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
            [
                "1.0.0",
                "2.0.0",
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
        ),
        (
            o.MINOR,
            3,
            [
                "1.0.0",
                "2.0.0",
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
            [
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
        ),
        (
            o.MICRO,
            3,
            [
                "1.0.0",
                "2.0.0",
                "2.1.0",
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
            [
                "2.1.1",
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
        ),
        (
            o.MINOR,
            3,
            [
                "2.2.0a1dev1",
                "2.2.0a1",
                "2.2.0",
                "1!1.0.0",
            ],
            [
                "2.2.0",
                "1!1.0.0",
            ],
        ),
    ],
)
def test_count(level: int, n: int, releases: Collection[str], expected: Collection[str]) -> None:
    release_set = fake_release_set(releases=releases, infer_successors=False)
    context = MagicMock(PackageContext)
    context.package = "compreq"
    count = o.count(level, n, release_set)

    assert fake_release_set(releases=expected, infer_successors=False) == count.resolve(context)
