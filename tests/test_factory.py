import pytest

import compreq.factory as f
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


def test_version() -> None:
    assert isinstance(f.version, VersionToken)
    assert isinstance(f.v, VersionToken)


@pytest.mark.parametrize(
    "requirement,expected",
    [
        (
            f.package("compreq"),
            LazyRequirement(
                package="compreq",
                url=None,
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            f.pkg("compreq"),
            LazyRequirement(
                package="compreq",
                url=None,
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            f.url("http://path/v1.2.3"),
            LazyRequirement(
                package=None,
                url="http://path/v1.2.3",
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            f.extra("extra"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra"},
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            f.specifier(">=1.2.3"),
            get_lazy_specifier(">=1.2.3"),
        ),
        (
            f.specifier_set(">=1.2.3,<2.0.0"),
            get_lazy_specifier_set(">=1.2.3,<2.0.0"),
        ),
        (
            f.marker("python_version=='1.2.3'"),
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
    assert ProdLazyReleaseSet(AllLazyReleaseSet(None)) == f.releases()
    assert ProdLazyReleaseSet(AllLazyReleaseSet("compreq")) == f.releases("compreq")
    assert PreLazyReleaseSet(AllLazyReleaseSet(None)) == f.prereleases()
    assert PreLazyReleaseSet(AllLazyReleaseSet("compreq")) == f.prereleases("compreq")
    assert AllLazyReleaseSet(None) == f.devreleases()
    assert AllLazyReleaseSet("compreq") == f.devreleases("compreq")
