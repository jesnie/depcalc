from typing import Type
from unittest.mock import MagicMock

import pytest
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

import compreq as cr
from compreq import (
    AllLazyReleaseSet,
    AnyMarker,
    AnyRelease,
    AnyReleaseSet,
    AnyRequirement,
    AnyRequirementSet,
    AnySpecifier,
    AnySpecifierOperator,
    AnySpecifierSet,
    AnyVersion,
    Context,
    EagerLazyRelease,
    EagerLazyReleaseSet,
    EagerLazyRequirementSet,
    EagerLazyVersion,
    LazyRelease,
    LazyReleaseSet,
    LazyRequirement,
    LazyRequirementSet,
    LazySpecifier,
    LazySpecifierSet,
    LazyVersion,
    PackageContext,
    PreLazyReleaseSet,
    ProdLazyReleaseSet,
    ReleaseLazyVersion,
    ReleaseSet,
    RequirementSet,
    SpecifierLazyReleaseSet,
    SpecifierOperator,
    get_lazy_release,
    get_lazy_release_set,
    get_lazy_requirement,
    get_lazy_requirement_set,
    get_lazy_specifier,
    get_lazy_specifier_set,
    get_lazy_version,
    get_marker,
    get_specifier_operator,
)
from tests.utils import fake_release, fake_release_set


def test_eager_lazy_release() -> None:
    release = fake_release()
    lazy = EagerLazyRelease(release)

    context = MagicMock(PackageContext)
    assert "foo.bar" == lazy.get_package()
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
    lazy = EagerLazyReleaseSet(frozenset())
    context = MagicMock(PackageContext)
    context.package = "foo.bar"

    assert lazy.get_package() is None
    assert ReleaseSet("foo.bar", frozenset()) == lazy.resolve(context)


def test_eager_lazy_release_set() -> None:
    release_2 = fake_release(version="1.2.0")
    release_1 = fake_release(version="1.1.0", successor=release_2)

    lazy = EagerLazyReleaseSet(
        frozenset([get_lazy_release(release_1), get_lazy_release(release_2)])
    )
    context = MagicMock(PackageContext)
    context.package = "foo.bar"

    assert "foo.bar" == lazy.get_package()
    assert ReleaseSet("foo.bar", frozenset([release_1, release_2])) == lazy.resolve(context)


def test_all_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )

    lazy = AllLazyReleaseSet(None)
    context = MagicMock(PackageContext)
    context.package = "foo.bar"
    context.releases.return_value = releases

    assert lazy.get_package() is None
    assert fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    ) == lazy.resolve(context)
    context.releases.assert_called_once_with("foo.bar")


def test_all_lazy_release_set__package() -> None:
    releases = fake_release_set(
        package="foo", releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )

    lazy = AllLazyReleaseSet("foo")
    context = MagicMock(PackageContext)
    context.package = "foo.bar"
    context.releases.return_value = releases

    assert "foo" == lazy.get_package()
    assert (
        releases
        == fake_release_set(
            package="foo", releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
        )
        == lazy.resolve(context)
    )
    context.releases.assert_called_once_with("foo")


def test_prod_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )
    source = MagicMock(LazyReleaseSet)
    source.get_package.return_value = "foo"
    source.resolve.return_value = releases
    context = MagicMock(PackageContext)

    lazy = ProdLazyReleaseSet(source)

    assert "foo" == lazy.get_package()
    assert fake_release_set(releases=["1.2.0", "1.3.0"]) == lazy.resolve(context)
    source.resolve.assert_called_once_with(context)


def test_pre_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.3.0.rc1.dev1", "1.3.0.rc1", "1.3.0.dev1", "1.3.0"]
    )
    source = MagicMock(LazyReleaseSet)
    source.get_package.return_value = "foo"
    source.resolve.return_value = releases
    context = MagicMock(PackageContext)

    lazy = PreLazyReleaseSet(source)

    assert "foo" == lazy.get_package()
    assert fake_release_set(releases=["1.2.0", "1.3.0.rc1", "1.3.0"]) == lazy.resolve(context)
    source.resolve.assert_called_once_with(context)


def test_specifier_lazy_release_set() -> None:
    releases = fake_release_set(
        releases=["1.2.0", "1.2.1", "1.3.0", "1.3.1", "1.4.0", "2.0.0", "2.1.0"],
        infer_successors=False,
    )
    source = MagicMock(LazyReleaseSet)
    source.get_package.return_value = "foo"
    source.resolve.return_value = releases
    context = MagicMock(PackageContext)

    lazy = SpecifierLazyReleaseSet(source, get_lazy_specifier_set(">=1.3.0,<2.0.0"))

    assert "foo" == lazy.get_package()
    assert fake_release_set(
        releases=["1.3.0", "1.3.1", "1.4.0"],
        infer_successors=False,
    ) == lazy.resolve(context)
    source.resolve.assert_called_once_with(context)


@pytest.mark.parametrize(
    "release_set,expected",
    [
        (
            None,
            ProdLazyReleaseSet(AllLazyReleaseSet(None)),
        ),
        (
            "foo.bar",
            ProdLazyReleaseSet(AllLazyReleaseSet("foo.bar")),
        ),
        (
            fake_release(version="1.1.0"),
            EagerLazyReleaseSet(frozenset([EagerLazyRelease(fake_release(version="1.1.0"))])),
        ),
        (
            EagerLazyRelease(fake_release(version="1.2.0")),
            EagerLazyReleaseSet(frozenset([EagerLazyRelease(fake_release(version="1.2.0"))])),
        ),
        (
            ReleaseSet("foo.bar", frozenset()),
            EagerLazyReleaseSet(frozenset()),
        ),
        (
            ReleaseSet(
                "foo.bar",
                frozenset(
                    [
                        fake_release(version="1.3.0"),
                        fake_release(version="1.4.0"),
                    ]
                ),
            ),
            EagerLazyReleaseSet(
                frozenset(
                    [
                        EagerLazyRelease(fake_release(version="1.3.0")),
                        EagerLazyRelease(fake_release(version="1.4.0")),
                    ]
                )
            ),
        ),
        (
            EagerLazyReleaseSet(frozenset()),
            EagerLazyReleaseSet(frozenset()),
        ),
        (
            EagerLazyReleaseSet(
                frozenset(
                    [
                        EagerLazyRelease(fake_release(version="1.5.0")),
                        EagerLazyRelease(fake_release(version="1.6.0")),
                    ]
                ),
            ),
            EagerLazyReleaseSet(
                frozenset(
                    [
                        EagerLazyRelease(fake_release(version="1.5.0")),
                        EagerLazyRelease(fake_release(version="1.6.0")),
                    ]
                )
            ),
        ),
        (
            Specifier("==1.7.0"),
            SpecifierLazyReleaseSet(
                ProdLazyReleaseSet(AllLazyReleaseSet(None)),
                get_lazy_specifier_set("==1.7.0"),
            ),
        ),
        (
            get_lazy_specifier("==1.8.0"),
            SpecifierLazyReleaseSet(
                ProdLazyReleaseSet(AllLazyReleaseSet(None)),
                get_lazy_specifier_set("==1.8.0"),
            ),
        ),
        (
            SpecifierSet(">=1.9.1,<2.0.0"),
            SpecifierLazyReleaseSet(
                ProdLazyReleaseSet(AllLazyReleaseSet(None)),
                get_lazy_specifier_set(">=1.9.1,<2.0.0"),
            ),
        ),
        (
            get_lazy_specifier_set(">=1.10.2,<2.0.0"),
            SpecifierLazyReleaseSet(
                ProdLazyReleaseSet(AllLazyReleaseSet(None)),
                get_lazy_specifier_set(">=1.10.2,<2.0.0"),
            ),
        ),
        (
            Requirement("foo.bar>=1.11.1,<2.0.0"),
            SpecifierLazyReleaseSet(
                ProdLazyReleaseSet(AllLazyReleaseSet("foo.bar")),
                get_lazy_specifier_set(">=1.11.1,<2.0.0"),
            ),
        ),
        (
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set(">=1.12.3,<2.0.0"),
                marker=None,
            ),
            SpecifierLazyReleaseSet(
                ProdLazyReleaseSet(AllLazyReleaseSet("foo.bar")),
                get_lazy_specifier_set(">=1.12.3,<2.0.0"),
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

    lazy = LazySpecifierSet(frozenset([specifier_1, specifier_2]))

    context = MagicMock(PackageContext)
    assert SpecifierSet(">=1.2.3,<2.0.0") == lazy.resolve(context)
    specifier_1.resolve.assert_called_once_with(context)
    specifier_2.resolve.assert_called_once_with(context)


@pytest.mark.parametrize(
    "specifier_set,expected",
    [
        (">=1.1.0", LazySpecifierSet(frozenset([get_lazy_specifier(">=1.1.0")]))),
        (
            Specifier(">=1.2.0"),
            LazySpecifierSet(frozenset([get_lazy_specifier(">=1.2.0")])),
        ),
        (
            get_lazy_specifier(">=1.3.0"),
            LazySpecifierSet(frozenset([get_lazy_specifier(">=1.3.0")])),
        ),
        (
            SpecifierSet(">=1.4.0,<2.0.0"),
            LazySpecifierSet(
                frozenset([get_lazy_specifier(">=1.4.0"), get_lazy_specifier("<2.0.0")])
            ),
        ),
        (
            LazySpecifierSet(
                frozenset([get_lazy_specifier(">=1.5.0"), get_lazy_specifier("<2.0.0")])
            ),
            LazySpecifierSet(
                frozenset([get_lazy_specifier(">=1.5.0"), get_lazy_specifier("<2.0.0")])
            ),
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
        "foo.bar",
        None,
        frozenset(["extra_1", "extra_2"]),
        specifier_set,
        Marker("python_version>'2.0'"),
    )

    package_context = MagicMock(PackageContext)
    context = MagicMock(Context)
    context.for_package.return_value = package_context

    assert Requirement(
        "foo.bar[extra_1,extra_2]<2.0.0,>=1.2.3; python_version > '2.0'"
    ) == requirement.resolve(context)
    context.for_package.assert_called_once_with("foo.bar")
    specifier_set.resolve.assert_called_once_with(package_context)


def test_lazy_requirement__url() -> None:
    requirement = LazyRequirement(
        "foo.bar",
        "http://path1/path2",
        frozenset(),
        LazySpecifierSet(frozenset()),
        None,
    )

    package_context = MagicMock(PackageContext)
    context = MagicMock(Context)
    context.for_package.return_value = package_context

    assert Requirement("foo.bar@ http://path1/path2") == requirement.resolve(context)
    context.for_package.assert_called_once_with("foo.bar")


@pytest.mark.parametrize(
    "requirement,expected",
    [
        (
            "foo.bar",
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            "foo.bar==1.1.0",
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set("==1.1.0"),
                marker=None,
            ),
        ),
        (
            Specifier("==1.2.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set("==1.2.0"),
                marker=None,
            ),
        ),
        (
            get_lazy_specifier("==1.3.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set("==1.3.0"),
                marker=None,
            ),
        ),
        (
            SpecifierSet(">=1.4.0,<2.0.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                marker=None,
            ),
        ),
        (
            get_lazy_specifier_set(">=1.4.0,<2.0.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                marker=None,
            ),
        ),
        (
            Requirement("foo.bar[extra]==1.5.0; python_version > '2.0.0'"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=get_lazy_specifier_set("==1.5.0"),
                marker=Marker("python_version > '2.0.0'"),
            ),
        ),
        (
            Requirement("foo.bar@http://path/v1.6.0"),
            LazyRequirement(
                package="foo.bar",
                url="http://path/v1.6.0",
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=get_lazy_specifier_set("==1.7.0"),
                marker=Marker("python_version > '2.0.0'"),
            ),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=get_lazy_specifier_set("==1.7.0"),
                marker=Marker("python_version > '2.0.0'"),
            ),
        ),
        (
            LazyRequirement(
                package="foo.bar",
                url="http://path/v1.8.0",
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
            LazyRequirement(
                package="foo.bar",
                url="http://path/v1.8.0",
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
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
            cr.package("foo.bar"),
            cr.package("foo.bar"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.package("foo.bar"),
            cr.package("foo"),
            AssertionError,
        ),
        (
            cr.package("foo.bar"),
            cr.url("http://path/v1.3.0"),
            LazyRequirement(
                package="foo.bar",
                url="http://path/v1.3.0",
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.package("foo.bar"),
            cr.extra("extra1"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(["extra1"]),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.package("foo.bar"),
            cr.specifier(">1.5.0"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set(">1.5.0"),
                marker=None,
            ),
        ),
        (
            cr.package("foo.bar"),
            cr.specifier_set(">1.5.0"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set(">1.5.0"),
                marker=None,
            ),
        ),
        (
            cr.package("foo.bar"),
            cr.marker("python_version>'2.1'"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Url
        (
            cr.url("http://path/v2.0.0"),
            cr.package("foo.bar"),
            LazyRequirement(
                package="foo.bar",
                url="http://path/v2.0.0",
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.url("http://path/v2.0.0"),
            LazyRequirement(
                package=None,
                url="http://path/v2.0.0",
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.url("http://path/v1.3.0"),
            AssertionError,
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.extra("extra1"),
            LazyRequirement(
                package=None,
                url="http://path/v2.0.0",
                extras=frozenset(["extra1"]),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.specifier(">1.5.0"),
            AssertionError,
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.specifier_set(">1.5.0"),
            AssertionError,
        ),
        (
            cr.url("http://path/v2.0.0"),
            cr.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url="http://path/v2.0.0",
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Extra
        (
            cr.extra("extra"),
            cr.package("foo.bar"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.url("http://path/v1.3.0"),
            LazyRequirement(
                package=None,
                url="http://path/v1.3.0",
                extras=frozenset(["extra"]),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.extra("extra"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(["extra"]),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.extra("extra1"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(["extra", "extra1"]),
                specifier=LazySpecifierSet(frozenset()),
                marker=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.specifier(">1.5.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(["extra"]),
                specifier=get_lazy_specifier_set(">1.5.0"),
                marker=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.specifier_set(">1.5.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(["extra"]),
                specifier=get_lazy_specifier_set(">1.5.0"),
                marker=None,
            ),
        ),
        (
            cr.extra("extra"),
            cr.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(["extra"]),
                specifier=LazySpecifierSet(frozenset()),
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Specifier
        (
            cr.specifier("==2.0.0"),
            cr.package("foo.bar"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset([get_lazy_specifier("==2.0.0")])),
                marker=None,
            ),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.url("http://path/v1.3.0"),
            AssertionError,
        ),
        (
            cr.specifier("==2.0.0"),
            cr.extra("extra1"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(["extra1"]),
                specifier=get_lazy_specifier_set("==2.0.0"),
                marker=None,
            ),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.specifier("==2.0.0"),
            get_lazy_specifier_set("==2.0.0"),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.specifier(">1.5.0"),
            get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.specifier_set(">1.5.0"),
            get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            cr.specifier("==2.0.0"),
            cr.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set("==2.0.0"),
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Specifier set
        (
            cr.specifier_set("==2.0.0"),
            cr.package("foo.bar"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset([get_lazy_specifier("==2.0.0")])),
                marker=None,
            ),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.url("http://path/v1.3.0"),
            AssertionError,
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.extra("extra1"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(["extra1"]),
                specifier=get_lazy_specifier_set("==2.0.0"),
                marker=None,
            ),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.specifier(">1.5.0"),
            get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.specifier_set("==2.0.0"),
            get_lazy_specifier_set("==2.0.0"),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.specifier_set(">1.5.0"),
            get_lazy_specifier_set(">1.5.0,==2.0.0"),
        ),
        (
            cr.specifier_set("==2.0.0"),
            cr.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set("==2.0.0"),
                marker=Marker("python_version>'2.1'"),
            ),
        ),
        # Marker
        (
            cr.marker("python_version=='3.0'"),
            cr.package("foo.bar"),
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.url("http://path/v1.3.0"),
            LazyRequirement(
                package=None,
                url="http://path/v1.3.0",
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.extra("extra1"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(["extra1"]),
                specifier=LazySpecifierSet(frozenset()),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.specifier(">1.5.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set(">1.5.0"),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.specifier_set(">1.5.0"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=get_lazy_specifier_set(">1.5.0"),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.marker("python_version=='3.0'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
                marker=Marker("python_version=='3.0'"),
            ),
        ),
        (
            cr.marker("python_version=='3.0'"),
            cr.marker("python_version>'2.1'"),
            LazyRequirement(
                package=None,
                url=None,
                extras=frozenset(),
                specifier=LazySpecifierSet(frozenset()),
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


@pytest.mark.parametrize(
    "requirement_set,expected",
    [
        (
            "foo.bar",
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package="foo.bar",
                            url=None,
                            extras=frozenset(),
                            specifier=LazySpecifierSet(frozenset()),
                            marker=None,
                        )
                    ]
                )
            ),
        ),
        (
            "foo.bar==1.1.0",
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package="foo.bar",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set("==1.1.0"),
                            marker=None,
                        )
                    ]
                )
            ),
        ),
        (
            Specifier("==1.2.0"),
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package=None,
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set("==1.2.0"),
                            marker=None,
                        )
                    ]
                )
            ),
        ),
        (
            get_lazy_specifier("==1.3.0"),
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package=None,
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set("==1.3.0"),
                            marker=None,
                        )
                    ]
                )
            ),
        ),
        (
            SpecifierSet(">=1.4.0,<2.0.0"),
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package=None,
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                            marker=None,
                        )
                    ]
                )
            ),
        ),
        (
            get_lazy_specifier_set(">=1.4.0,<2.0.0"),
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package=None,
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set(">=1.4.0,<2.0.0"),
                            marker=None,
                        )
                    ]
                )
            ),
        ),
        (
            Requirement("foo.bar[extra]==1.5.0; python_version > '2.0.0'"),
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package="foo.bar",
                            url=None,
                            extras=frozenset(["extra"]),
                            specifier=get_lazy_specifier_set("==1.5.0"),
                            marker=Marker("python_version > '2.0.0'"),
                        )
                    ]
                )
            ),
        ),
        (
            LazyRequirement(
                package="foo.bar",
                url=None,
                extras=frozenset(["extra"]),
                specifier=get_lazy_specifier_set("==1.7.0"),
                marker=Marker("python_version > '2.0.0'"),
            ),
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package="foo.bar",
                            url=None,
                            extras=frozenset(["extra"]),
                            specifier=get_lazy_specifier_set("==1.7.0"),
                            marker=Marker("python_version > '2.0.0'"),
                        )
                    ]
                )
            ),
        ),
        (
            [
                Requirement("foo>=1.2.3"),
                Requirement("bar==2.0.0"),
            ],
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                        ),
                        LazyRequirement(
                            package="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                        ),
                    ]
                ),
            ),
        ),
        (
            {
                "foo": Requirement("foo>=1.2.3"),
                "bar": Requirement("bar==2.0.0"),
            },
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                        ),
                        LazyRequirement(
                            package="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                        ),
                    ]
                ),
            ),
        ),
        (
            RequirementSet.new(
                [
                    Requirement("foo>=1.2.3"),
                    Requirement("bar==2.0.0"),
                ],
            ),
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                        ),
                        LazyRequirement(
                            package="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                        ),
                    ]
                ),
            ),
        ),
        (
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                        ),
                        LazyRequirement(
                            package="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                        ),
                    ]
                ),
            ),
            EagerLazyRequirementSet(
                frozenset(
                    [
                        LazyRequirement(
                            package="foo",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set(">=1.2.3"),
                            marker=None,
                        ),
                        LazyRequirement(
                            package="bar",
                            url=None,
                            extras=frozenset(),
                            specifier=get_lazy_specifier_set("==2.0.0"),
                            marker=None,
                        ),
                    ]
                ),
            ),
        ),
    ],
)
def test_get_lazy_requirement_set(
    requirement_set: AnyRequirementSet, expected: LazyRequirementSet
) -> None:
    assert get_lazy_requirement_set(requirement_set) == expected
