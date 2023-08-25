# pylint: disable=redefined-outer-name

import datetime as dt
from dataclasses import dataclass, replace
from itertools import chain
from typing import Final, Iterable

from dateutil.relativedelta import relativedelta
from packaging.version import Version

from compreq.contexts import PackageContext
from compreq.lazy import (
    EMPTY_REQUIREMENT,
    AllLazyReleaseSet,
    AnyMarker,
    AnyReleaseSet,
    AnySpecifier,
    AnySpecifierSet,
    AnyVersion,
    LazyRelease,
    LazyReleaseSet,
    LazyRequirement,
    LazySpecifier,
    LazySpecifierSet,
    LazyVersion,
    PreLazyReleaseSet,
    ProdLazyReleaseSet,
    get_lazy_release_set,
    get_lazy_specifier,
    get_lazy_specifier_set,
    get_lazy_version,
    get_marker,
)
from compreq.levels import AnyLevel, IntLevel, Level, get_level
from compreq.releases import Release, ReleaseSet
from compreq.time import UtcDatetime
from compreq.versiontokens import VersionToken

version: Final[VersionToken] = VersionToken()
"""
Token for building a version specifier. Example::

    package("compreq") & version(">=", "1.2.3")

See also: `v`, `specifier`, `specifier_set`.
"""


v: Final[VersionToken] = version
"""
Token for building a version specifier. Example::

    pkg("compreq") & v(">=", "1.2.3")

See also: `version`, `specifier`, specifier_set`.
"""


def package(value: str) -> LazyRequirement:
    """
    Create a `LazyRequirement` with this package. Example::

        package("compreq") & version(">=", "1.2.3")
    """
    return replace(EMPTY_REQUIREMENT, package=value)


def pkg(value: str) -> LazyRequirement:
    """
    Create a `LazyRequirement` with this package. Example::

        pkg("compreq") & v(">=", "1.2.3")
    """
    return replace(EMPTY_REQUIREMENT, package=value)


def url(value: str) -> LazyRequirement:
    """
    Create a `LazyRequirement` with this URL. Example::

        pkg("compreq") & url("https://...")
    """
    return replace(EMPTY_REQUIREMENT, url=value)


def extra(value: str) -> LazyRequirement:
    """
    Create a `LazyRequirement` with this extra. Example::

        pkg("compreq") & extra("torch") & extra("tensorflow")
    """
    return replace(EMPTY_REQUIREMENT, extras=frozenset([value]))


def specifier(value: AnySpecifier) -> LazySpecifier:
    """
    Create a `LazyRequirement` with this version specifier. Example::

        pkg("compreq") & specifier(">=1.2.3")

    See also: `version`, `v`, `specifier_set`.
    """
    return get_lazy_specifier(value)


def specifier_set(value: AnySpecifierSet) -> LazySpecifierSet:
    """
    Create a `LazyRequirement` with this version specifier set. Example::

        pkg("compreq") & specifier_set("<2.0.0,>=1.2.3")

    See also: `version`, `v`, `specifier`.
    """
    return get_lazy_specifier_set(value)


def marker(value: AnyMarker) -> LazyRequirement:
    """
    Create a `LazyRequirement` conditional on this marker. Example::

        pkg("compreq") & marker("platform_system != 'Darwin' or platform_machine != 'arm64'")
    """
    return replace(EMPTY_REQUIREMENT, marker=get_marker(value))


def releases(package: str | None = None) -> LazyReleaseSet:
    """
    Returns the set of all "production" releases of this package.

    :param package: Package to get releases of. If `None`, the package is determined from the
    context.
    """
    return ProdLazyReleaseSet(AllLazyReleaseSet(package))


def prereleases(
    package: str | None = None,
) -> LazyReleaseSet:
    """
    Returns the set of all "production" and pre-releases of this package. (No dev-releases.)

    :param package: Package to get releases of. If `None`, the package is determined from the
    context.
    """
    return PreLazyReleaseSet(AllLazyReleaseSet(package))


def devreleases(
    package: str | None = None,
) -> LazyReleaseSet:
    """
    Returns the set of all "production", pre-, and dev-releases releases of this package.

    :param package: Package to get releases of. If `None`, the package is determined from the
    context.
    """
    return AllLazyReleaseSet(package)


@dataclass(order=True, frozen=True)
class MinLazyRelease(LazyRelease):
    """
    Strategy for getting the release with the minimal version.

    See also: `min_ver`, `MaxLazyRelease`, `MinimumLazyVersion`
    """

    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> Release:
        release_set = self.release_set.resolve(context)
        return min(release_set)


def min_ver(release_set: AnyReleaseSet | None = None) -> LazyRelease:
    """
    Get the release with the minimal version.

    See also: `max_ver`, `MinLazyRelease`, `minimum_ver`

    :param release_set: Set of releases to get minimum of. If `None`, all production releases of the
        package in the context is used.
    """
    return MinLazyRelease(get_lazy_release_set(release_set))


@dataclass(order=True, frozen=True)
class MaxLazyRelease(LazyRelease):
    """
    Strategy for getting the release with the maximal version.

    See also: `max_ver`, `MinLazyRelease`, `MaximumLazyVersion`
    """

    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> Release:
        release_set = self.release_set.resolve(context)
        return max(release_set)


def max_ver(release_set: AnyReleaseSet | None = None) -> LazyRelease:
    """
    Get the release with the maximal version.

    See also: `min_ver`, `MaxLazyRelease`, `maximum_ver`

    :param release_set: Set of releases to get maximum of. If `None`, all production releases of the
        package in the context is used.
    """
    return MaxLazyRelease(get_lazy_release_set(release_set))


@dataclass(order=True, frozen=True)
class MinimumLazyVersion(LazyVersion):
    """
    Strategy for getting the minimal of a fixed set of versions.

    See also: `minimum_ver`, `MinLazyRelease`, `MaximumLazyVersion`
    """

    versions: tuple[LazyVersion, ...]

    def resolve(self, context: PackageContext) -> Version:
        return min(v.resolve(context) for v in self.versions)


def minimum_ver(*versions: AnyVersion) -> LazyVersion:
    """
    Get the minimal version from a fixed set of versions.

    See also: `min_ver`, `MinimumLazyVersion`, `maximum_ver`

    :param release_set: Set of releases to get minimum of. If `None`, all production releases of the
        package in the context is used.
    """
    return MinimumLazyVersion(tuple(get_lazy_version(v) for v in versions))


@dataclass(order=True, frozen=True)
class MaximumLazyVersion(LazyVersion):
    """
    Strategy for getting the maximal of a fixed set of versions.

    See also: `maximum_ver`, `MaxLazyRelease`, `MinimumLazyVersion`
    """

    versions: tuple[LazyVersion, ...]

    def resolve(self, context: PackageContext) -> Version:
        return max(v.resolve(context) for v in self.versions)


def maximum_ver(*versions: AnyVersion) -> LazyVersion:
    """
    Get the maximal version from a fixed set of versions.

    See also: `max_ver`, `MaximumLazyVersion`, `minimum_ver`

    :param release_set: Set of releases to get maximum of. If `None`, all production releases of the
        package in the context is used.
    """
    return MaximumLazyVersion(tuple(get_lazy_version(v) for v in versions))


@dataclass(order=True, frozen=True)
class CeilLazyVersion(LazyVersion):
    """
    Round a version up at a given level.
    """

    level: Level
    version: LazyVersion
    keep_trailing_zeros: bool

    def resolve(self, context: PackageContext) -> Version:
        version = self.version.resolve(context)
        return self.ceil(self.level, version, self.keep_trailing_zeros)

    @staticmethod
    def ceil(level: Level, version: Version, keep_trailing_zeros: bool) -> Version:
        """
        Round a version up at a given level.

        In practice this means incrementing the value at the given level, and removing all following
        levels. For example::

            CeilLazyVersion.ceil(MAJOR, Version("1.2.3"), False) == Version("2")
            CeilLazyVersion.ceil(MINOR, Version("1.2.3"), False) == Version("1.3")

        Set `keep_trailing_zeros` to `True` to keep the trailing elements::

            CeilLazyVersion.ceil(MAJOR, Version("1.2.3"), True) == Version("2.0.0")
            CeilLazyVersion.ceil(MINOR, Version("1.2.3"), True) == Version("1.3.0")
        """
        release = version.release
        i = level.index(version)
        ceil_release: Iterable[int] = chain(release[:i], [release[i] + 1])
        if keep_trailing_zeros:
            ceil_release = chain(ceil_release, (0 for _ in release[i + 1 :]))
        return Version(f"{version.epoch}!" + ".".join(str(r) for r in ceil_release))


def ceil_ver(
    level: AnyLevel, version: AnyVersion, keep_trailing_zeros: bool = False
) -> LazyVersion:
    """
    Round a version up at a given level.

    In practice this means incrementing the value at the given level, and removing all following
    levels. For example::

        ceil_ver(MAJOR, "1.2.3") == Version("2")
        ceil_ver(MINOR, "1.2.3") == Version("1.3")

    Set `keep_trailing_zeros` to `True` to keep the trailing elements::

        ceil_ver(MAJOR, "1.2.3", True) == Version("2.0.0")
        ceil_ver(MINOR, "1.2.3", True) == Version("1.3.0")
    """
    return CeilLazyVersion(get_level(level), get_lazy_version(version), keep_trailing_zeros)


@dataclass(order=True, frozen=True)
class FloorLazyVersion(LazyVersion):
    """
    Round a version down at a given level.
    """

    level: Level
    version: LazyVersion
    keep_trailing_zeros: bool

    def resolve(self, context: PackageContext) -> Version:
        version = self.version.resolve(context)
        return self.floor(self.level, version, self.keep_trailing_zeros)

    @staticmethod
    def floor(level: Level, version: Version, keep_trailing_zeros: bool) -> Version:
        """
        Round a version down at a given level.

        In practice this means removing all levels after the given one. For example::

            FloorLazyVersion.floor(MAJOR, Version("1.2.3"), False) == Version("1")
            FloorLazyVersion.floor(MINOR, Version("1.2.3"), False) == Version("1.2")

        Set `keep_trailing_zeros` to `True` to keep the trailing elements::

            FloorLazyVersion.floor(MAJOR, Version("1.2.3"), True) == Version("1.0.0")
            FloorLazyVersion.floor(MINOR, Version("1.2.3"), True) == Version("1.2.0")
        """
        release = version.release
        i = level.index(version)
        floor_release: Iterable[int] = release[: i + 1]
        if keep_trailing_zeros:
            floor_release = chain(floor_release, (0 for _ in release[i + 1 :]))
        return Version(f"{version.epoch}!" + ".".join(str(r) for r in floor_release))


def floor_ver(
    level: AnyLevel, version: AnyVersion, keep_trailing_zeros: bool = False
) -> LazyVersion:
    """
    Round a version down at a given level.

    In practice this means removing all levels after the given one. For example::

        floor_ver(MAJOR, "1.2.3") == Version("1")
        floor_ver(MINOR, "1.2.3") == Version("1.2")

    Set `keep_trailing_zeros` to `True` to keep the trailing elements::

        floor_ver(MAJOR, "1.2.3", True) == Version("1.0.0")
        floor_ver(MINOR, "1.2.3", True) == Version("1.2.0")
    """
    return FloorLazyVersion(get_level(level), get_lazy_version(version), keep_trailing_zeros)


@dataclass(order=True, frozen=True)
class MinAgeLazyReleaseSet(LazyReleaseSet):
    """Strategy for computing all releases that have at least the given age."""

    now: UtcDatetime | None
    min_age: dt.timedelta | relativedelta
    allow_empty: bool
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)

        now = self.now or context.now
        max_time = now - self.min_age

        result = frozenset(r for r in release_set if r.released_time <= max_time)
        if not (self.allow_empty or result):
            result = frozenset({min(release_set)})
        return ReleaseSet(package=release_set.package, releases=result)


def min_age(
    release_set: AnyReleaseSet | None = None,
    *,
    now: UtcDatetime | None = None,
    age: dt.timedelta | relativedelta | None = None,
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    allow_empty: bool = False,
) -> MinAgeLazyReleaseSet:
    """
    Get all releases that are older than a given age.

    The age can be configured, either by setting the `age` parameter, or by setting one or more of
    `years`, `months`, `weeks`, `days`, `hours`, `minutes` or `seconds`.

    :param release_set: Set of releases to filter by age. If `None`, all production releases of the
        package in the context is used.
    :param now: The point in time to compute age relative to. If unset the current time of the
        context is used.
    :param allow_empty: Whether to allow returning the empty set. If `False` and no releases are old
        enough, the single oldest release is returned.
    """
    if age is None:
        age = relativedelta(
            years=years,
            months=months,
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )
    return MinAgeLazyReleaseSet(now, age, allow_empty, get_lazy_release_set(release_set))


@dataclass(order=True, frozen=True)
class MaxAgeLazyReleaseSet(LazyReleaseSet):
    """Strategy for computing all releases that have at most the given age."""

    now: UtcDatetime | None
    max_age: dt.timedelta | relativedelta
    allow_empty: bool
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)

        now = self.now or context.now
        min_time = now - self.max_age

        result = frozenset(r for r in release_set if r.released_time >= min_time)
        if not (self.allow_empty or result):
            result = frozenset({max(release_set)})
        return ReleaseSet(package=release_set.package, releases=result)


def max_age(
    release_set: AnyReleaseSet | None = None,
    *,
    now: UtcDatetime | None = None,
    age: dt.timedelta | relativedelta | None = None,
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    allow_empty: bool = False,
) -> MaxAgeLazyReleaseSet:
    """
    Get all releases that are younger than a given age.

    The age can be configured, either by setting the `age` parameter, or by setting one or more of
    `years`, `months`, `weeks`, `days`, `hours`, `minutes` or `seconds`.

    :param release_set: Set of releases to filter by age. If `None`, all production releases of the
        package in the context is used.
    :param now: The point in time to compute age relative to. If unset the current time of the
        context is used.
    :param allow_empty: Whether to allow returning the empty set. If `False` and no releases are
        young enough, the single youngest release is returned.
    """
    if age is None:
        age = relativedelta(
            years=years,
            months=months,
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )
    return MaxAgeLazyReleaseSet(now, age, allow_empty, get_lazy_release_set(release_set))


@dataclass(order=True, frozen=True)
class CountLazyReleaseSet(LazyReleaseSet):
    """Strategy for computing the most recent n releases at a certain level."""

    level: Level
    n: int
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)
        fixed_level = IntLevel(self.level.index(max(release_set).version))
        unique_versions_at_level = {
            FloorLazyVersion.floor(fixed_level, r.version, keep_trailing_zeros=False)
            for r in release_set
        }
        min_version = sorted(unique_versions_at_level, reverse=True)[: self.n][-1]
        result = frozenset(r for r in release_set if r.version >= min_version)
        return ReleaseSet(package=release_set.package, releases=result)


def count(
    level: AnyLevel,
    n: int,
    release_set: AnyReleaseSet | None = None,
) -> LazyReleaseSet:
    """
    Get the most recent `n` releases at a certain level.

    For example, to get the three most recent minor releases::

        count(MINOR, 3)

    :param release_set: Set of releases to filter by age. If `None`, all production releases of the
        package in the context is used.
    """
    return CountLazyReleaseSet(get_level(level), n, get_lazy_release_set(release_set))
