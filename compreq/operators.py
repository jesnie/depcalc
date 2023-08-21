# pylint: disable=redefined-outer-name

import datetime as dt
from dataclasses import dataclass, replace
from itertools import chain
from typing import Final, Iterable

from dateutil.relativedelta import relativedelta
from packaging.version import Version

from compreq.context import PackageContext
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
from compreq.levels import (
    AnyLevel,
    IntLevel,
    Level,
    RelativeToFirstNonZeroLevel,
    get_level,
)
from compreq.release import Release, ReleaseSet
from compreq.time import UtcDatetime
from compreq.versiontoken import VersionToken

MAJOR: Final[Level] = IntLevel(0)
MINOR: Final[Level] = IntLevel(1)
MICRO: Final[Level] = IntLevel(2)
REL_MAJOR: Final[Level] = RelativeToFirstNonZeroLevel(0)
REL_MINOR: Final[Level] = RelativeToFirstNonZeroLevel(1)
REL_MICRO: Final[Level] = RelativeToFirstNonZeroLevel(3)


version: Final[VersionToken] = VersionToken()
v: Final[VersionToken] = version


def package(value: str) -> LazyRequirement:
    return replace(EMPTY_REQUIREMENT, package=value)


def pkg(value: str) -> LazyRequirement:
    return replace(EMPTY_REQUIREMENT, package=value)


def url(value: str) -> LazyRequirement:
    return replace(EMPTY_REQUIREMENT, url=value)


def extra(value: str) -> LazyRequirement:
    return replace(EMPTY_REQUIREMENT, extras={value})


def specifier(value: AnySpecifier) -> LazySpecifier:
    return get_lazy_specifier(value)


def specifier_set(value: AnySpecifierSet) -> LazySpecifierSet:
    return get_lazy_specifier_set(value)


def marker(value: AnyMarker) -> LazyRequirement:
    return replace(EMPTY_REQUIREMENT, marker=get_marker(value))


def releases(package: str | None = None) -> LazyReleaseSet:
    return ProdLazyReleaseSet(AllLazyReleaseSet(package))


def prereleases(
    package: str | None = None,
) -> LazyReleaseSet:
    return PreLazyReleaseSet(AllLazyReleaseSet(package))


def devreleases(
    package: str | None = None,
) -> LazyReleaseSet:
    return AllLazyReleaseSet(package)


@dataclass(order=True, frozen=True)
class MinLazyRelease(LazyRelease):
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> Release:
        release_set = self.release_set.resolve(context)
        return min(release_set.releases)


def min_ver(release_set: AnyReleaseSet | None = None) -> LazyRelease:
    return MinLazyRelease(get_lazy_release_set(release_set))


@dataclass(order=True, frozen=True)
class MaxLazyRelease(LazyRelease):
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> Release:
        release_set = self.release_set.resolve(context)
        return max(release_set.releases)


def max_ver(release_set: AnyReleaseSet | None = None) -> LazyRelease:
    return MaxLazyRelease(get_lazy_release_set(release_set))


@dataclass(order=True, frozen=True)
class MinimumLazyVersion(LazyVersion):
    versions: tuple[LazyVersion, ...]

    def resolve(self, context: PackageContext) -> Version:
        return min(v.resolve(context) for v in self.versions)


def minimum_ver(*versions: AnyVersion) -> LazyVersion:
    return MinimumLazyVersion(tuple(get_lazy_version(v) for v in versions))


@dataclass(order=True, frozen=True)
class MaximumLazyVersion(LazyVersion):
    versions: tuple[LazyVersion, ...]

    def resolve(self, context: PackageContext) -> Version:
        return max(v.resolve(context) for v in self.versions)


def maximum_ver(*versions: AnyVersion) -> LazyVersion:
    return MaximumLazyVersion(tuple(get_lazy_version(v) for v in versions))


@dataclass(order=True, frozen=True)
class CeilLazyVersion(LazyVersion):
    level: Level
    version: LazyVersion
    keep_trailing_zeros: bool

    def resolve(self, context: PackageContext) -> Version:
        version = self.version.resolve(context)
        return self.ceil(self.level, version, self.keep_trailing_zeros)

    @staticmethod
    def ceil(level: Level, version: Version, keep_trailing_zeros: bool) -> Version:
        release = version.release
        i = level.index(version)
        ceil_release: Iterable[int] = chain(release[:i], [release[i] + 1])
        if keep_trailing_zeros:
            ceil_release = chain(ceil_release, (0 for _ in release[i + 1 :]))
        return Version(f"{version.epoch}!" + ".".join(str(r) for r in ceil_release))


def ceil_ver(
    level: AnyLevel, version: AnyVersion, keep_trailing_zeros: bool = False
) -> LazyVersion:
    return CeilLazyVersion(get_level(level), get_lazy_version(version), keep_trailing_zeros)


@dataclass(order=True, frozen=True)
class FloorLazyVersion(LazyVersion):
    level: Level
    version: LazyVersion
    keep_trailing_zeros: bool

    def resolve(self, context: PackageContext) -> Version:
        version = self.version.resolve(context)
        return self.floor(self.level, version, self.keep_trailing_zeros)

    @staticmethod
    def floor(level: Level, version: Version, keep_trailing_zeros: bool) -> Version:
        release = version.release
        i = level.index(version)
        floor_release: Iterable[int] = release[: i + 1]
        if keep_trailing_zeros:
            floor_release = chain(floor_release, (0 for _ in release[i + 1 :]))
        return Version(f"{version.epoch}!" + ".".join(str(r) for r in floor_release))


def floor_ver(
    level: AnyLevel, version: AnyVersion, keep_trailing_zeros: bool = False
) -> LazyVersion:
    return FloorLazyVersion(get_level(level), get_lazy_version(version), keep_trailing_zeros)


@dataclass(order=True, frozen=True)
class MinAgeLazyReleaseSet(LazyReleaseSet):
    now: UtcDatetime | None
    min_age: dt.timedelta | relativedelta
    allow_empty: bool
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)

        now = self.now or context.now
        max_time = now - self.min_age

        result = {r for r in release_set.releases if r.released_time <= max_time}
        if not (self.allow_empty or result):
            result = {min(release_set.releases)}
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
    now: UtcDatetime | None
    max_age: dt.timedelta | relativedelta
    allow_empty: bool
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)

        now = self.now or context.now
        min_time = now - self.max_age

        result = {r for r in release_set.releases if r.released_time >= min_time}
        if not (self.allow_empty or result):
            result = {max(release_set.releases)}
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
    level: Level
    n: int
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)
        fixed_level = IntLevel(self.level.index(max(release_set.releases).version))
        unique_versions_at_level = {
            FloorLazyVersion.floor(fixed_level, r.version, keep_trailing_zeros=False)
            for r in release_set.releases
        }
        min_version = sorted(unique_versions_at_level, reverse=True)[: self.n][-1]
        result = {r for r in release_set.releases if r.version >= min_version}
        return ReleaseSet(package=release_set.package, releases=result)


def count(
    level: AnyLevel,
    n: int,
    release_set: AnyReleaseSet | None = None,
) -> LazyReleaseSet:
    return CountLazyReleaseSet(get_level(level), n, get_lazy_release_set(release_set))
