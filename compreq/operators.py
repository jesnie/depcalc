# pylint: disable=redefined-outer-name

import datetime as dt
from dataclasses import dataclass, replace
from itertools import chain

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
from compreq.release import Release, ReleaseSet
from compreq.versiontoken import VersionToken

MAJOR = 0
MINOR = 1
MICRO = 2


version = VersionToken()
v = version


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
    level: int
    version: LazyVersion

    def resolve(self, context: PackageContext) -> Version:
        version = self.version.resolve(context)
        return self.ceil(self.level, version)

    @staticmethod
    def ceil(level: int, version: Version) -> Version:
        release = version.release
        ceil_release = chain(
            release[:level],
            [release[level] + 1],
            (0 for _ in release[level + 1 :]),
        )
        return Version(f"{version.epoch}!" + ".".join(str(r) for r in ceil_release))


def ceil_ver(level: int, version: AnyVersion) -> LazyVersion:
    return CeilLazyVersion(level, get_lazy_version(version))


@dataclass(order=True, frozen=True)
class FloorLazyVersion(LazyVersion):
    level: int
    version: LazyVersion

    def resolve(self, context: PackageContext) -> Version:
        version = self.version.resolve(context)
        return self.floor(self.level, version)

    @staticmethod
    def floor(level: int, version: Version) -> Version:
        release = version.release
        floor_release = chain(
            release[: level + 1],
            (0 for _ in release[level + 1 :]),
        )
        return Version(f"{version.epoch}!" + ".".join(str(r) for r in floor_release))


def floor_ver(level: int, version: AnyVersion) -> LazyVersion:
    return FloorLazyVersion(level, get_lazy_version(version))


@dataclass(order=True, frozen=True)
class MinAgeLazyReleaseSet(LazyReleaseSet):
    now: dt.datetime | None
    min_age: dt.timedelta
    allow_empty: bool
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)

        # TODO(jesnie): Get `now` from context.
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) if self.now is None else self.now
        max_time = now - self.min_age

        result = {r for r in release_set.releases if r.released_time <= max_time}
        if not (self.allow_empty or result):
            result = {min(release_set.releases)}
        return ReleaseSet(package=release_set.package, releases=result)


def min_age(
    release_set: AnyReleaseSet | None = None,
    *,
    now: dt.datetime | None = None,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    allow_empty: bool = False,
) -> MinAgeLazyReleaseSet:
    # TODO(jesnie): Support months and years?
    return MinAgeLazyReleaseSet(
        now,
        dt.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds),
        allow_empty,
        get_lazy_release_set(release_set),
    )


@dataclass(order=True, frozen=True)
class MaxAgeLazyReleaseSet(LazyReleaseSet):
    now: dt.datetime | None
    max_age: dt.timedelta
    allow_empty: bool
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)

        # TODO(jesnie): Get `now` from context.
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) if self.now is None else self.now
        min_time = now - self.max_age

        result = {r for r in release_set.releases if r.released_time >= min_time}
        if not (self.allow_empty or result):
            result = {max(release_set.releases)}
        return ReleaseSet(package=release_set.package, releases=result)


def max_age(
    release_set: AnyReleaseSet | None = None,
    *,
    now: dt.datetime | None = None,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    allow_empty: bool = False,
) -> MaxAgeLazyReleaseSet:
    # TODO(jesnie): Support months and years?
    return MaxAgeLazyReleaseSet(
        now,
        dt.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds),
        allow_empty,
        get_lazy_release_set(release_set),
    )


@dataclass(order=True, frozen=True)
class CountLazyReleaseSet(LazyReleaseSet):
    level: int
    n: int
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)
        unique_versions_at_level = {
            FloorLazyVersion.floor(self.level, r.version) for r in release_set.releases
        }
        min_version = sorted(unique_versions_at_level, reverse=True)[: self.n][-1]
        result = {r for r in release_set.releases if r.version >= min_version}
        return ReleaseSet(package=release_set.package, releases=result)


def count(
    level: int,
    n: int,
    release_set: AnyReleaseSet | None = None,
) -> LazyReleaseSet:
    return CountLazyReleaseSet(level, n, get_lazy_release_set(release_set))
