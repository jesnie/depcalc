import datetime as dt
from dataclasses import dataclass
from itertools import chain

from packaging.version import Version

from depcalc.context import PackageContext
from depcalc.lazy import (
    AnyReleaseSet,
    AnyVersion,
    LazyRelease,
    LazyReleaseSet,
    LazyVersion,
    get_lazy_release_set,
    get_lazy_version,
)
from depcalc.release import Release, ReleaseSet

MAJOR = 0
MINOR = 1
MICRO = 2


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
class CeilLazyVersion(LazyVersion):
    level: int
    version: LazyVersion

    def resolve(self, context: PackageContext) -> Version:
        version = self.version.resolve(context)
        release = version.release
        ceil_release = chain(
            release[: self.level],
            [release[self.level] + 1],
            (0 for _ in release[self.level + 1 :]),
        )
        return Version(".".join(str(r) for r in ceil_release))


def ceil_ver(level: int, version: AnyVersion) -> LazyVersion:
    return CeilLazyVersion(level, get_lazy_version(version))


@dataclass(order=True, frozen=True)
class FloorLazyVersion(LazyVersion):
    level: int
    version: LazyVersion

    def resolve(self, context: PackageContext) -> Version:
        version = self.version.resolve(context)
        release = version.release
        floor_release = chain(
            release[: self.level + 1],
            (0 for _ in release[self.level + 1 :]),
        )
        return Version(".".join(str(r) for r in floor_release))


def floor_ver(level: int, version: AnyVersion) -> LazyVersion:
    return FloorLazyVersion(level, get_lazy_version(version))


@dataclass(order=True, frozen=True)
class MinAgeLazyReleaseSet(LazyReleaseSet):
    now: dt.datetime | None
    min_age: dt.timedelta
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)

        # TODO(jesnie): Get `now` from context.
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) if self.now is None else self.now
        max_time = now - self.min_age

        return ReleaseSet(
            package=release_set.package,
            releases={r for r in release_set.releases if r.released_time <= max_time},
        )


def min_age(
    *,
    now: dt.datetime | None = None,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    release_set: AnyReleaseSet | None = None,
) -> MinAgeLazyReleaseSet:
    # TODO(jesnie): Support months and years?
    return MinAgeLazyReleaseSet(
        now,
        dt.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds),
        get_lazy_release_set(release_set),
    )


@dataclass(order=True, frozen=True)
class MaxAgeLazyReleaseSet(LazyReleaseSet):
    now: dt.datetime | None
    max_age: dt.timedelta
    release_set: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)

        # TODO(jesnie): Get `now` from context.
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) if self.now is None else self.now
        max_time = now - self.max_age

        return ReleaseSet(
            package=release_set.package,
            releases={r for r in release_set.releases if r.released_time <= max_time},
        )


def max_age(
    *,
    now: dt.datetime | None = None,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    release_set: AnyReleaseSet | None = None,
) -> MaxAgeLazyReleaseSet:
    # TODO(jesnie): Support months and years?
    return MaxAgeLazyReleaseSet(
        now,
        dt.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds),
        get_lazy_release_set(release_set),
    )
