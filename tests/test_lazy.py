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
    AnySpecifierSet,
    AnyVersion,
    DevLazyReleaseSet,
    EagerLazyRelease,
    EagerLazyReleaseSet,
    EagerLazyVersion,
    LazyRelease,
    LazyReleaseSet,
    LazyRequirement,
    LazySpecifier,
    LazySpecifierSet,
    LazyVersion,
    PreLazyReleaseSet,
    ProdLazyReleaseSet,
    ReleaseLazyVersion,
    SpecifierOperator,
    get_lazy_release,
    get_lazy_release_set,
    get_lazy_requirement,
    get_lazy_specifier,
    get_lazy_specifier_set,
    get_lazy_version,
    get_marker,
    get_specifier_operator,
)
from depcalc.release import ReleaseSet
from tests.utils import fake_release, fake_release_set


def test_eager_lazy_release() -> None:
    release = fake_release()
    lazy = EagerLazyRelease(release)

    context = MagicMock(PackageContext)
    assert release == lazy.resolve(context)


@pytest.mark.parametrize(
    "release,expected",
    [
        (
            fake_release(version="1.1.0"),
            EagerLazyRelease(fake_release(version="1.1.0")),
        ),
        (
            EagerLazyRelease(fake_release(version="1.2.0")),
            EagerLazyRelease(fake_release(version="1.2.0")),
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
    release_2 = fake_release(version="1.2.0")
    release_1 = fake_release(version="1.1.0", successor=release_2)

    lazy = EagerLazyReleaseSet({get_lazy_release(release_1), get_lazy_release(release_2)})
    context = MagicMock(PackageContext)
    context.package = "depcalc"

    assert ReleaseSet("depcalc", {release_1, release_2}) == lazy.resolve(context)


def test_prod_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )

    lazy = ProdLazyReleaseSet(None)
    context = MagicMock(PackageContext)
    context.package = "depcalc"
    context.releases.return_value = releases

    assert fake_release_set(releases=["1.2.0", "1.3.0"]) == lazy.resolve(context)
    context.releases.assert_called_once_with("depcalc")


def test_prod_lazy_release_set__package() -> None:
    releases = fake_release_set(
        package="foo", releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )

    lazy = ProdLazyReleaseSet("foo")
    context = MagicMock(PackageContext)
    context.package = "depcalc"
    context.releases.return_value = releases

    assert fake_release_set(package="foo", releases=["1.2.0", "1.3.0"]) == lazy.resolve(context)
    context.releases.assert_called_once_with("foo")


def test_pre_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )

    lazy = PreLazyReleaseSet(None)
    context = MagicMock(PackageContext)
    context.package = "depcalc"
    context.releases.return_value = releases

    assert fake_release_set(releases=["1.2.0", "1.3.0.rc1", "1.3.0"]) == lazy.resolve(context)
    context.releases.assert_called_once_with("depcalc")


def test_pre_lazy_release_set__package() -> None:
    releases = fake_release_set(
        package="foo", releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )

    lazy = PreLazyReleaseSet("foo")
    context = MagicMock(PackageContext)
    context.package = "depcalc"
    context.releases.return_value = releases

    assert fake_release_set(
        package="foo", releases=["1.2.0", "1.3.0.rc1", "1.3.0"]
    ) == lazy.resolve(context)
    context.releases.assert_called_once_with("foo")


def test_dev_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )

    lazy = DevLazyReleaseSet(None)
    context = MagicMock(PackageContext)
    context.package = "depcalc"
    context.releases.return_value = releases

    assert fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    ) == lazy.resolve(context)
    context.releases.assert_called_once_with("depcalc")


def test_dev_lazy_release_set__package() -> None:
    releases = fake_release_set(
        package="foo", releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )

    lazy = DevLazyReleaseSet("foo")
    context = MagicMock(PackageContext)
    context.package = "depcalc"
    context.releases.return_value = releases

    assert (
        releases
        == fake_release_set(
            package="foo", releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
        )
        == lazy.resolve(context)
    )
    context.releases.assert_called_once_with("foo")


@pytest.mark.parametrize(
    "release_set,expected",
    [
        (
            None,
            ProdLazyReleaseSet(None),
        ),
        (
            fake_release(version="1.1.0"),
            EagerLazyReleaseSet({EagerLazyRelease(fake_release(version="1.1.0"))}),
        ),
        (
            EagerLazyRelease(fake_release(version="1.2.0")),
            EagerLazyReleaseSet({EagerLazyRelease(fake_release(version="1.2.0"))}),
        ),
        (
            ReleaseSet("depcalc", set()),
            EagerLazyReleaseSet(set()),
        ),
        (
            ReleaseSet(
                "depcalc",
                {
                    fake_release(version="1.3.0"),
                    fake_release(version="1.4.0"),
                },
            ),
            EagerLazyReleaseSet(
                {
                    EagerLazyRelease(fake_release(version="1.3.0")),
                    EagerLazyRelease(fake_release(version="1.4.0")),
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
                    EagerLazyRelease(fake_release(version="1.5.0")),
                    EagerLazyRelease(fake_release(version="1.6.0")),
                },
            ),
            EagerLazyReleaseSet(
                {
                    EagerLazyRelease(fake_release(version="1.5.0")),
                    EagerLazyRelease(fake_release(version="1.6.0")),
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
    release = EagerLazyRelease(fake_release(version=version))
    lazy = ReleaseLazyVersion(release)

    context = MagicMock(PackageContext)
    assert version == lazy.resolve(context)


@pytest.mark.parametrize(
    "version,expected",
    [
        ("1.0.0", EagerLazyVersion(Version("1.0.0"))),
        (
            fake_release(version="1.1.0"),
            EagerLazyVersion(Version("1.1.0")),
        ),
        (
            EagerLazyRelease(
                fake_release(version="1.2.0"),
            ),
            ReleaseLazyVersion(
                EagerLazyRelease(
                    fake_release(version="1.2.0"),
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
    lazy = LazySpecifier(op, version)

    context = MagicMock(PackageContext)
    assert Specifier("<1.5.0") == lazy.resolve(context)
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


def test_lazy_specifier_set() -> None:
    specifier_1 = MagicMock(LazySpecifier)
    specifier_1.resolve.return_value = Specifier(">=1.2.3")
    specifier_2 = MagicMock(LazySpecifier)
    specifier_2.resolve.return_value = Specifier("<2.0.0")

    lazy = LazySpecifierSet({specifier_1, specifier_2})

    context = MagicMock(PackageContext)
    assert SpecifierSet(">=1.2.3,<2.0.0") == lazy.resolve(context)
    specifier_1.resolve.assert_called_once_with(context)
    specifier_2.resolve.assert_called_once_with(context)


@pytest.mark.parametrize(
    "specifier_set,expected",
    [
        (">=1.1.0", LazySpecifierSet({get_lazy_specifier(">=1.1.0")})),
        (
            Specifier(">=1.2.0"),
            LazySpecifierSet({get_lazy_specifier(">=1.2.0")}),
        ),
        (
            get_lazy_specifier(">=1.3.0"),
            LazySpecifierSet({get_lazy_specifier(">=1.3.0")}),
        ),
        (
            SpecifierSet(">=1.4.0,<2.0.0"),
            LazySpecifierSet({get_lazy_specifier(">=1.4.0"), get_lazy_specifier("<2.0.0")}),
        ),
        (
            LazySpecifierSet({get_lazy_specifier(">=1.5.0"), get_lazy_specifier("<2.0.0")}),
            LazySpecifierSet({get_lazy_specifier(">=1.5.0"), get_lazy_specifier("<2.0.0")}),
        ),
    ],
)
def test_get_lazy_specifier_set(specifier_set: AnySpecifierSet, expected: LazySpecifierSet) -> None:
    assert get_lazy_specifier_set(specifier_set) == expected


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
    specifier_set = MagicMock(LazySpecifierSet)
    specifier_set.resolve.return_value = SpecifierSet(">=1.2.3,<2.0.0")
    requirement = LazyRequirement(
        "depcalc",
        None,
        {"extra_1", "extra_2"},
        specifier_set,
        Marker("python_version>'2.0'"),
    )

    package_context = MagicMock(PackageContext)
    context = MagicMock(Context)
    context.for_package.return_value = package_context

    assert Requirement(
        "depcalc[extra_1,extra_2]<2.0.0,>=1.2.3; python_version > '2.0'"
    ) == requirement.resolve(context)
    context.for_package.assert_called_once_with("depcalc")
    specifier_set.resolve.assert_called_once_with(package_context)


def test_lazy_requirement__url() -> None:
    requirement = LazyRequirement(
        "depcalc",
        "http://path1/path2",
        set(),
        LazySpecifierSet(set()),
        None,
    )

    package_context = MagicMock(PackageContext)
    context = MagicMock(Context)
    context.for_package.return_value = package_context

    assert Requirement("depcalc@ http://path1/path2") == requirement.resolve(context)
    context.for_package.assert_called_once_with("depcalc")


@pytest.mark.parametrize(
    "requirement,expected",
    [
        (
            "depcalc",
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            "depcalc==1.1.0",
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier=get_lazy_specifier_set("==1.1.0"),
                marker=None,
            ),
        ),
        (
            Specifier("==1.2.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=get_lazy_specifier_set("==1.2.0"),
                marker=None,
            ),
        ),
        (
            get_lazy_specifier("==1.3.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=get_lazy_specifier_set("==1.3.0"),
                marker=None,
            ),
        ),
        (
            SpecifierSet(">=1.4.0,<2.0.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                marker=None,
            ),
        ),
        (
            get_lazy_specifier_set(">=1.4.0,<2.0.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                marker=None,
            ),
        ),
        (
            Requirement("depcalc[extra]==1.5.0; python_version > '2.0.0'"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras={"extra"},
                specifier=get_lazy_specifier_set("==1.5.0"),
                marker=Marker("python_version > '2.0.0'"),
            ),
        ),
        (
            Requirement("depcalc@http://path/v1.6.0"),
            LazyRequirement(
                package="depcalc",
                url="http://path/v1.6.0",
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
        (
            LazyRequirement(
                package="depcalc",
                url=None,
                extras={"extra"},
                specifier=get_lazy_specifier_set("==1.7.0"),
                marker=Marker("python_version > '2.0.0'"),
            ),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras={"extra"},
                specifier=get_lazy_specifier_set("==1.7.0"),
                marker=Marker("python_version > '2.0.0'"),
            ),
        ),
        (
            LazyRequirement(
                package="depcalc",
                url="http://path/v1.8.0",
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
            LazyRequirement(
                package="depcalc",
                url="http://path/v1.8.0",
                extras=set(),
                specifier=LazySpecifierSet(set()),
                marker=None,
            ),
        ),
    ],
)
def test_get_lazy_requirement(requirement: AnyRequirement, expected: LazyRequirement) -> None:
    assert get_lazy_requirement(requirement) == expected


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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=get_lazy_specifier_set(">1.5.0"),
                marker=None,
            ),
        ),
        (
            f.package("depcalc"),
            f.specifier_set(">1.5.0"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier=get_lazy_specifier_set(">1.5.0"),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
            f.specifier_set(">1.5.0"),
            AssertionError,
        ),
        (
            f.url("http://path/v2.0.0"),
            f.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url="http://path/v2.0.0",
                extras=set(),
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=get_lazy_specifier_set(">1.5.0"),
                marker=None,
            ),
        ),
        (
            f.extra("extra"),
            f.specifier_set(">1.5.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra"},
                specifier=get_lazy_specifier_set(">1.5.0"),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet({get_lazy_specifier("==2.0.0")}),
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
                specifier=get_lazy_specifier_set("==2.0.0"),
                marker=None,
            ),
        ),
        (
            f.specifier("==2.0.0"),
            f.specifier("==2.0.0"),
            get_lazy_specifier_set("==2.0.0"),
        ),
        (
            f.specifier("==2.0.0"),
            f.specifier(">1.5.0"),
            get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            f.specifier("==2.0.0"),
            f.specifier_set(">1.5.0"),
            get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            f.specifier("==2.0.0"),
            f.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=get_lazy_specifier_set("==2.0.0"),
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Specifier set
        (
            f.specifier_set("==2.0.0"),
            f.package("depcalc"),
            LazyRequirement(
                package="depcalc",
                url=None,
                extras=set(),
                specifier=LazySpecifierSet({get_lazy_specifier("==2.0.0")}),
                marker=None,
            ),
        ),
        (
            f.specifier_set("==2.0.0"),
            f.url("http://path/v1.3.0"),
            AssertionError,
        ),
        (
            f.specifier_set("==2.0.0"),
            f.extra("extra1"),
            LazyRequirement(
                package=None,
                url=None,
                extras={"extra1"},
                specifier=get_lazy_specifier_set("==2.0.0"),
                marker=None,
            ),
        ),
        (
            f.specifier_set("==2.0.0"),
            f.specifier(">1.5.0"),
            get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            f.specifier_set("==2.0.0"),
            f.specifier_set("==2.0.0"),
            get_lazy_specifier_set("==2.0.0"),
        ),
        (
            f.specifier_set("==2.0.0"),
            f.specifier_set(">1.5.0"),
            get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            f.specifier_set("==2.0.0"),
            f.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=get_lazy_specifier_set("==2.0.0"),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=get_lazy_specifier_set(">1.5.0"),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            f.marker("python_version=='3.0'"),
            f.specifier_set(">1.5.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=set(),
                specifier=get_lazy_specifier_set(">1.5.0"),
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
                specifier=LazySpecifierSet(set()),
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
                specifier=LazySpecifierSet(set()),
                marker=Marker("python_version=='3.0' and python_version>'2.1'"),
            ),
        ),
    ],
)
def test_compose(
    lhs: LazyRequirement,
    rhs: LazyRequirement,
    expected: LazyRequirement | LazySpecifierSet | Type[Exception],
) -> None:
    if isinstance(expected, type):
        with pytest.raises(expected):
            lhs & rhs  # pylint: disable=pointless-statement
    else:
        assert (lhs & rhs) == expected
