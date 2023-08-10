import datetime as dt
from typing import Type
from unittest.mock import MagicMock

import pytest
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

import depcalc.factory as f
from depcalc.context import Context, PackageContext
from depcalc.lazy import (
    AnyMarker,
    AnyRelease,
    AnyReleaseSet,
    AnyRequirement,
    AnySpecifier,
    AnySpecifierOperator,
    AnyVersion,
    EagerLazyRelease,
    EagerLazyReleaseSet,
    EagerLazyVersion,
    LazyRelease,
    LazyReleaseSet,
    LazyRequirement,
    LazySpecifier,
    LazyVersion,
    RawLazyReleaseSet,
    ReleaseLazyVersion,
    SpecifierOperator,
    get_lazy_release,
    get_lazy_release_set,
    get_lazy_requirement,
    get_lazy_specifier,
    get_lazy_version,
    get_marker,
    get_specifier_operator,
)
from depcalc.release import Release, ReleaseSet


def test_eager_lazy_release() -> None:
    release = Release(
        package="depcalc",
        version=Version("3.1.2"),
        released_time=dt.datetime(2023, 8, 7, 2, 1),
        successor=None,
    )
    lazy = EagerLazyRelease(release)

    context = MagicMock(PackageContext)
    assert release == lazy.resolve(context)


@pytest.mark.parametrize(
    "release,expected",
    [
        (
            Release(
                package="depcalc",
                version=Version("1.1.0"),
                released_time=dt.datetime(2023, 8, 7, 13, 45),
                successor=None,
            ),
            EagerLazyRelease(
                Release(
                    package="depcalc",
                    version=Version("1.1.0"),
                    released_time=dt.datetime(2023, 8, 7, 13, 45),
                    successor=None,
                ),
            ),
        ),
        (
            EagerLazyRelease(
                Release(
                    package="depcalc",
                    version=Version("1.2.0"),
                    released_time=dt.datetime(2023, 8, 7, 13, 45),
                    successor=None,
                ),
            ),
            EagerLazyRelease(
                Release(
                    package="depcalc",
                    version=Version("1.2.0"),
                    released_time=dt.datetime(2023, 8, 7, 13, 45),
                    successor=None,
                ),
            ),
        ),
    ],
)
def test_get_lazy_release(release: AnyRelease, expected: LazyRelease) -> None:
    assert expected == get_lazy_release(release)


def test_eager_lazy_release_set__empty() -> None:
    lazy = EagerLazyReleaseSet(set())
    context = MagicMock(PackageContext)
    context.package = "depcalc"

    assert ReleaseSet("depcalc", set()) == lazy.resolve(context)


def test_eager_lazy_release_set() -> None:
    release_2 = Release(
        package="depcalc",
        version=Version("1.2.0"),
        released_time=dt.datetime(2023, 8, 7, 14, 11),
        successor=None,
    )
    release_1 = Release(
        package="depcalc",
        version=Version("1.1.0"),
        released_time=dt.datetime(2023, 8, 7, 13, 45),
        successor=release_2,
    )

    lazy = EagerLazyReleaseSet({get_lazy_release(release_1), get_lazy_release(release_2)})
    context = MagicMock(PackageContext)
    context.package = "depcalc"

    assert ReleaseSet("depcalc", {release_1, release_2}) == lazy.resolve(context)


def test_raw_lazy_release_set() -> None:
    releases = MagicMock(ReleaseSet)

    lazy = RawLazyReleaseSet(None)
    context = MagicMock(PackageContext)
    context.package = "depcalc"
    context.releases.return_value = releases

    assert releases == lazy.resolve(context)
    context.releases.assert_called_once_with("depcalc")


def test_raw_lazy_release_set__package() -> None:
    releases = MagicMock(ReleaseSet)

    lazy = RawLazyReleaseSet("foo")
    context = MagicMock(PackageContext)
    context.package = "depcalc"
    context.releases.return_value = releases

    assert releases == lazy.resolve(context)
    context.releases.assert_called_once_with("foo")


@pytest.mark.parametrize(
    "release_set,expected",
    [
        (
            None,
            RawLazyReleaseSet(None),
        ),
        (
            Release(
                package="depcalc",
                version=Version("1.1.0"),
                released_time=dt.datetime(2023, 8, 7, 13, 45),
                successor=None,
            ),
            EagerLazyReleaseSet(
                {
                    EagerLazyRelease(
                        Release(
                            package="depcalc",
                            version=Version("1.1.0"),
                            released_time=dt.datetime(2023, 8, 7, 13, 45),
                            successor=None,
                        ),
                    )
                }
            ),
        ),
        (
            EagerLazyRelease(
                Release(
                    package="depcalc",
                    version=Version("1.2.0"),
                    released_time=dt.datetime(2023, 8, 7, 13, 45),
                    successor=None,
                ),
            ),
            EagerLazyReleaseSet(
                {
                    EagerLazyRelease(
                        Release(
                            package="depcalc",
                            version=Version("1.2.0"),
                            released_time=dt.datetime(2023, 8, 7, 13, 45),
                            successor=None,
                        ),
                    )
                }
            ),
        ),
        (
            ReleaseSet("depcalc", set()),
            EagerLazyReleaseSet(set()),
        ),
        (
            ReleaseSet(
                "depcalc",
                {
                    Release(
                        package="depcalc",
                        version=Version("1.3.0"),
                        released_time=dt.datetime(2023, 8, 7, 13, 45),
                        successor=None,
                    ),
                    Release(
                        package="depcalc",
                        version=Version("1.4.0"),
                        released_time=dt.datetime(2023, 8, 7, 14, 23),
                        successor=None,
                    ),
                },
            ),
            EagerLazyReleaseSet(
                {
                    EagerLazyRelease(
                        Release(
                            package="depcalc",
                            version=Version("1.3.0"),
                            released_time=dt.datetime(2023, 8, 7, 13, 45),
                            successor=None,
                        ),
                    ),
                    EagerLazyRelease(
                        Release(
                            package="depcalc",
                            version=Version("1.4.0"),
                            released_time=dt.datetime(2023, 8, 7, 14, 23),
                            successor=None,
                        ),
                    ),
                }
            ),
        ),
        (
            EagerLazyReleaseSet(set()),
            EagerLazyReleaseSet(set()),
        ),
        (
            EagerLazyReleaseSet(
                {
                    EagerLazyRelease(
                        Release(
                            package="depcalc",
                            version=Version("1.5.0"),
                            released_time=dt.datetime(2023, 8, 7, 13, 45),
                            successor=None,
                        ),
                    ),
                    EagerLazyRelease(
                        Release(
                            package="depcalc",
                            version=Version("1.6.0"),
                            released_time=dt.datetime(2023, 8, 7, 14, 23),
                            successor=None,
                        ),
                    ),
                },
            ),
            EagerLazyReleaseSet(
                {
                    EagerLazyRelease(
                        Release(
                            package="depcalc",
                            version=Version("1.5.0"),
                            released_time=dt.datetime(2023, 8, 7, 13, 45),
                            successor=None,
                        ),
                    ),
                    EagerLazyRelease(
                        Release(
                            package="depcalc",
                            version=Version("1.6.0"),
                            released_time=dt.datetime(2023, 8, 7, 14, 23),
                            successor=None,
                        ),
                    ),
                }
            ),
        ),
    ],
)
def test_get_lazy_release_set(release_set: AnyReleaseSet, expected: LazyReleaseSet) -> None:
    assert expected == get_lazy_release_set(release_set)


def test_eager_lazy_version() -> None:
    version = Version("1.1.0")
    lazy = EagerLazyVersion(version)

    context = MagicMock(PackageContext)
    assert version == lazy.resolve(context)


def test_release_lazy_version() -> None:
    version = Version("3.1.2")
    release = EagerLazyRelease(
        Release(
            package="depcalc",
            version=version,
            released_time=dt.datetime(2023, 8, 7, 2, 1),
            successor=None,
        )
    )
    lazy = ReleaseLazyVersion(release)

    context = MagicMock(PackageContext)
    assert version == lazy.resolve(context)


@pytest.mark.parametrize(
    "version,expected",
    [
        ("1.0.0", EagerLazyVersion(Version("1.0.0"))),
        (
            Release(
                package="depcalc",
                version=Version("1.1.0"),
                released_time=dt.datetime(2023, 8, 7, 13, 45),
                successor=None,
            ),
            EagerLazyVersion(Version("1.1.0")),
        ),
        (
            EagerLazyRelease(
                Release(
                    package="depcalc",
                    version=Version("1.2.0"),
                    released_time=dt.datetime(2023, 8, 7, 13, 45),
                    successor=None,
                )
            ),
            ReleaseLazyVersion(
                EagerLazyRelease(
                    Release(
                        package="depcalc",
                        version=Version("1.2.0"),
                        released_time=dt.datetime(2023, 8, 7, 13, 45),
                        successor=None,
                    )
                )
            ),
        ),
        (Version("1.3.0"), EagerLazyVersion(Version("1.3.0"))),
        (EagerLazyVersion(Version("1.4.0")), EagerLazyVersion(Version("1.4.0"))),
    ],
)
def test_get_lazy_version(version: AnyVersion, expected: LazyVersion) -> None:
    assert expected == get_lazy_version(version)


@pytest.mark.parametrize(
    "op,expected",
    [
        ("~=", SpecifierOperator.COMPATIBLE),
        (SpecifierOperator.NE, SpecifierOperator.NE),
    ],
)
def test_get_specifier_operator(op: AnySpecifierOperator, expected: SpecifierOperator) -> None:
    assert get_specifier_operator(op) == expected


def test_lazy_specifier() -> None:
    op = SpecifierOperator.LT
    version = MagicMock(LazyVersion)
    version.resolve.return_value = Version("1.5.0")
    specifier = LazySpecifier(op, version)

    context = MagicMock(PackageContext)
    assert Specifier("<1.5.0") == specifier.resolve(context)
    version.resolve.assert_called_once_with(context)


@pytest.mark.parametrize(
    "specifier,expected",
    [
        (">=1.1.0", LazySpecifier(SpecifierOperator.GE, EagerLazyVersion(Version("1.1.0")))),
        (
            Specifier(">=1.2.0"),
            LazySpecifier(SpecifierOperator.GE, EagerLazyVersion(Version("1.2.0"))),
        ),
        (
            LazySpecifier(SpecifierOperator.GE, EagerLazyVersion(Version("1.3.0"))),
            LazySpecifier(SpecifierOperator.GE, EagerLazyVersion(Version("1.3.0"))),
        ),
    ],
)
def test_get_lazy_specifier(specifier: AnySpecifier, expected: LazySpecifier) -> None:
    assert get_lazy_specifier(specifier) == expected


@pytest.mark.parametrize(
    "marker,expected",
    [
        ("python_version > '1.0'", Marker("python_version > '1.0'")),
        (Marker("python_version > '1.1'"), Marker("python_version > '1.1'")),
    ],
)
def test_get_marker(marker: AnyMarker, expected: Marker) -> None:
    assert get_marker(marker) == expected


def test_lazy_requirement__specifier() -> None:
    specifier_1 = MagicMock(LazySpecifier)
    specifier_1.resolve.return_value = Specifier(">=1.2.3")
    specifier_1.__lt__.side_effect = lambda rhs: True
    specifier_2 = MagicMock(LazySpecifier)
    specifier_2.resolve.return_value = Specifier("<2.0.0")
    specifier_2.__lt__.side_effect = lambda rhs: False
    requirement = LazyRequirement(
        "depcalc",
        None,
        {"extra_1", "extra_2"},
        {specifier_1, specifier_2},
        Marker("python_version>'2.0'"),
    )

    package_context = MagicMock(PackageContext)
    context = MagicMock(Context)
    context.for_package.return_value = package_context

    assert Requirement(
        "depcalc[extra_1,extra_2]<2.0.0,>=1.2.3; python_version > '2.0'"
    ) == requirement.resolve(context)
    context.for_package.assert_called_once_with("depcalc")
    specifier_1.resolve.assert_called_once_with(package_context)
    specifier_2.resolve.assert_called_once_with(package_context)


def test_lazy_requirement__url() -> None:
    requirement = LazyRequirement(
        "depcalc",
        "http://path1/path2",
        set(),
        set(),
        None,
    )

    package_context = MagicMock(PackageContext)
    context = MagicMock(Context)
    context.for_package.return_value = package_context

    assert Requirement("depcalc@ http://path1/path2") == requirement.resolve(context)
    context.for_package.assert_called_once_with("depcalc")


@pytest.mark.parametrize(
    "lhs,rhs,expected",
    [
        # Package
        (
            f.package("depcalc"),
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
            f.package("depcalc"),
            f.package("foo"),
            AssertionError,
        ),
        (
            f.package("depcalc"),
            f.url("http://path/v1.3.0"),
            LazyRequirement(
                package="depcalc",
                url="http://path/v1.3.0",
                extras=set(),
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.package("depcalc"),
            f.extra("extra1"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras={"extra1"},
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.package("depcalc"),
            f.specifier(">1.5.0"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier={get_lazy_specifier(">1.5.0")},
                marker=None,
            ),
        ),
        (
            f.package("depcalc"),
            f.marker("python_version>'2.1'"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier=set(),
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Url
        (
            f.url("http://path/v2.0.0"),
            f.package("depcalc"),
            LazyRequirement(
                package="depcalc",
                url="http://path/v2.0.0",
                extras=set(),
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.url("http://path/v2.0.0"),
            f.url("http://path/v2.0.0"),
            LazyRequirement(
                package=None,
                url="http://path/v2.0.0",
                extras=set(),
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.url("http://path/v2.0.0"),
            f.url("http://path/v1.3.0"),
            AssertionError,
        ),
        (
            f.url("http://path/v2.0.0"),
            f.extra("extra1"),
            LazyRequirement(
                package=None,
                url="http://path/v2.0.0",
                extras={"extra1"},
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.url("http://path/v2.0.0"),
            f.specifier(">1.5.0"),
            AssertionError,
        ),
        (
            f.url("http://path/v2.0.0"),
            f.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url="http://path/v2.0.0",
                extras=set(),
                specifier=set(),
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Extra
        (
            f.extra("extra"),
            f.package("depcalc"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras={"extra"},
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.extra("extra"),
            f.url("http://path/v1.3.0"),
            LazyRequirement(
                package=None,
                url="http://path/v1.3.0",
                extras={"extra"},
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.extra("extra"),
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
            f.extra("extra"),
            f.extra("extra1"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra", "extra1"},
                specifier=set(),
                marker=None,
            ),
        ),
        (
            f.extra("extra"),
            f.specifier(">1.5.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra"},
                specifier={get_lazy_specifier(">1.5.0")},
                marker=None,
            ),
        ),
        (
            f.extra("extra"),
            f.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra"},
                specifier=set(),
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Specifier
        (
            f.specifier("==2.0.0"),
            f.package("depcalc"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier={get_lazy_specifier("==2.0.0")},
                marker=None,
            ),
        ),
        (
            f.specifier("==2.0.0"),
            f.url("http://path/v1.3.0"),
            AssertionError,
        ),
        (
            f.specifier("==2.0.0"),
            f.extra("extra1"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra1"},
                specifier={get_lazy_specifier("==2.0.0")},
                marker=None,
            ),
        ),
        (
            f.specifier("==2.0.0"),
            f.specifier("==2.0.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier={get_lazy_specifier("==2.0.0")},
                marker=None,
            ),
        ),
        (
            f.specifier("==2.0.0"),
            f.specifier(">1.5.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier={get_lazy_specifier(">1.5.0"), get_lazy_specifier("==2.0.0")},
                marker=None,
            ),
        ),
        (
            f.specifier("==2.0.0"),
            f.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier={get_lazy_specifier("==2.0.0")},
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Marker
        (
            f.marker("python_version=='3.0'"),
            f.package("depcalc"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier=set(),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            f.marker("python_version=='3.0'"),
            f.url("http://path/v1.3.0"),
            LazyRequirement(
                package=None,
                url="http://path/v1.3.0",
                extras=set(),
                specifier=set(),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            f.marker("python_version=='3.0'"),
            f.extra("extra1"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra1"},
                specifier=set(),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            f.marker("python_version=='3.0'"),
            f.specifier(">1.5.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier={get_lazy_specifier(">1.5.0")},
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            f.marker("python_version=='3.0'"),
            f.marker("python_version=='3.0'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=set(),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            f.marker("python_version=='3.0'"),
            f.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=set(),
                marker=Marker("python_version=='3.0' and python_version>'2.1'"),
            ),
        ),
    ],
)
def test_lazy_requirement__compose(
    lhs: LazyRequirement, rhs: LazyRequirement, expected: LazyRequirement | Type[Exception]
) -> None:
    if isinstance(expected, LazyRequirement):
        assert (lhs & rhs) == expected
    else:
        assert isinstance(expected, type)
        with pytest.raises(expected):
            lhs & rhs  # pylint: disable=pointless-statement


@pytest.mark.parametrize(
    "requirement,expected",
    [
        (
            "depcalc",
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier=set(),
                marker=None,
            ),
        ),
        (
            "depcalc==1.1.0",
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier={get_lazy_specifier("==1.1.0")},
                marker=None,
            ),
        ),
        (
            Specifier("==1.2.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier={get_lazy_specifier("==1.2.0")},
                marker=None,
            ),
        ),
        (
            get_lazy_specifier("==1.3.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier={get_lazy_specifier("==1.3.0")},
                marker=None,
            ),
        ),
        (
            SpecifierSet(">=1.4.0,<2.0.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier={get_lazy_specifier(">=1.4.0"), get_lazy_specifier("<2.0.0")},
                marker=None,
            ),
        ),
        (
            Requirement("depcalc[extra]==1.5.0; python_version > '2.0.0'"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras={"extra"},
                specifier={get_lazy_specifier("==1.5.0")},
                marker=Marker("python_version > '2.0.0'"),
            ),
        ),
        (
            Requirement("depcalc@http://path/v1.6.0"),
            LazyRequirement(
                package="depcalc",
                url="http://path/v1.6.0",
                extras=set(),
                specifier=set(),
                marker=None,
            ),
        ),
        (
            LazyRequirement(
                package="depcalc",
                url=None,
                extras={"extra"},
                specifier={get_lazy_specifier("==1.7.0")},
                marker=Marker("python_version > '2.0.0'"),
            ),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras={"extra"},
                specifier={get_lazy_specifier("==1.7.0")},
                marker=Marker("python_version > '2.0.0'"),
            ),
        ),
        (
            LazyRequirement(
                package="depcalc",
                url="http://path/v1.8.0",
                extras=set(),
                specifier=set(),
                marker=None,
            ),
            LazyRequirement(
                package="depcalc",
                url="http://path/v1.8.0",
                extras=set(),
                specifier=set(),
                marker=None,
            ),
        ),
    ],
)
def test_get_lazy_requirement(requirement: AnyRequirement, expected: LazyRequirement) -> None:
    assert get_lazy_requirement(requirement) == expected
