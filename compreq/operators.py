# pylint: disable=redefined-outer-name

import datetime as dt
from dataclasses import dataclass, replace
from typing import Final

from dateutil.relativedelta import relativedelta
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from compreq.bounds import get_bounds
from compreq.contexts import Context, PackageContext
from compreq.factory import make_requirement
from compreq.lazy import (
    EMPTY_REQUIREMENT,
    AllLazyReleaseSet,
    AnyMarker,
    AnyReleaseSet,
    AnyRequirementSet,
    AnySpecifier,
    AnySpecifierSet,
    AnyVersion,
    LazyRelease,
    LazyReleaseSet,
    LazyRequirement,
    LazyRequirementSet,
    LazySpecifier,
    LazySpecifierSet,
    LazyVersion,
    PreLazyReleaseSet,
    ProdLazyReleaseSet,
    get_lazy_release_set,
    get_lazy_requirement_set,
    get_lazy_specifier,
    get_lazy_specifier_set,
    get_lazy_version,
    get_marker,
)
from compreq.levels import AnyLevel, IntLevel, Level, get_level
from compreq.releases import Release, ReleaseSet
from compreq.requirements import RequirementSet
from compreq.rounding import ceil, floor
from compreq.time import UtcDatetime
from compreq.versiontokens import VersionToken
from compreq.virtualenv import temp_venv

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

    def get_package(self) -> str | None:
        return self.release_set.get_package()

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

    def get_package(self) -> str | None:
        return self.release_set.get_package()

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
        return ceil(self.level, version, self.keep_trailing_zeros)


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
        return floor(self.level, version, self.keep_trailing_zeros)


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

    def get_package(self) -> str | None:
        return self.release_set.get_package()

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

    def get_package(self) -> str | None:
        return self.release_set.get_package()

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

    def get_package(self) -> str | None:
        return self.release_set.get_package()

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.release_set.resolve(context)
        fixed_level = IntLevel(self.level.index(max(release_set).version))
        unique_versions_at_level = {
            floor(fixed_level, r.version, keep_trailing_zeros=False) for r in release_set
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


@dataclass(order=True, frozen=True)
class RequirementsLazyRequirementSet(LazyRequirementSet):
    """
    Get all the requirements of a release.
    """

    package: str
    """
    The package to get requiremts of.
    """

    release: LazyReleaseSet
    """
    Release to get requirements of.

    This must resolve to exactly one actual release.
    """

    def resolve(self, context: Context) -> RequirementSet:
        python_version = context.default_python
        pcontext = context.for_package(self.package)
        releases = self.release.resolve(pcontext)
        assert len(releases) == 1, releases
        (release,) = releases.releases
        requirement = Requirement(f"{release.package}=={release.version}")
        requirement_set = RequirementSet.new([requirement])

        with temp_venv(python_version) as venv:
            venv.install(requirement_set, deps=False)
            return venv.package_metadata(release.package).requires


def requirements(release_set: AnyReleaseSet, package: str | None = None) -> LazyRequirementSet:
    """
    Returns the requirments of the given release.

    If the package cannot be derived from the `release` directly, you must set `package`.
    """
    lazy = get_lazy_release_set(release_set)
    if package is None:
        package = lazy.get_package()
    assert package is not None, release_set
    return RequirementsLazyRequirementSet(package, lazy)


@dataclass(order=True, frozen=True)
class ConsistentLowerBoundsLazyRequirementSet(LazyRequirementSet):
    """
    Loosens lower bounds, to make them consistent.
    """

    requirement_set: LazyRequirementSet

    def resolve(self, context: Context) -> RequirementSet:
        requirement_set = self.requirement_set.resolve(context)
        bounds = {}
        result = []
        upper_bounds = []
        python: Requirement | None = None
        for requirement in requirement_set.values():
            package = requirement.name
            if package == "python":
                python = requirement
            elif requirement.specifier:
                b = get_bounds(requirement.specifier)
                bounds[package] = b
                if b.lower and b.lower_inclusive:
                    upper_bounds.append(
                        make_requirement(
                            requirement,
                            specifier=SpecifierSet(f"<={b.lower}") & b.exclusions_specifier_set(),
                            marker=None,
                        )
                    )
                else:
                    result.append(requirement)
            else:
                result.append(requirement)

        if python:
            b = get_bounds(python.specifier)
            assert b.lower and b.lower_inclusive, python
            python_version = b.lower
        else:
            python_version = context.default_python

        with temp_venv(python_version) as venv:
            venv.install(RequirementSet.new(result + upper_bounds))

            for ub in upper_bounds:
                package = ub.name
                b = bounds[package]
                assert b.lower, b
                version = venv.package_metadata(package).version
                assert b.lower >= version, (b, version)
                specifiers = replace(b, lower=version).minimal_specifier_set()
                result.append(make_requirement(requirement_set[package], specifier=specifiers))

        if python:
            result.append(python)

        return RequirementSet.new(result)


def consistent_lower_bounds(requirement_set: AnyRequirementSet) -> LazyRequirementSet:
    """
    Loosens lower bounds, to make them consistent.

    For example: Assume you depend on two packages: foo and bar, with these releases:

    * `foo 1.0.0`
    * `foo 1.1.0`
    * `foo 1.2.0`
    * `bar 2.1.0`, requires `foo<1.1.0,>=1.0.0`
    * `bar 2.2.0`, requires `foo<1.2.0,>=1.1.0`

    You depend on `foo>=1.1.0` and `bar>=2.1.0`. While this constraint can be satisfied by `foo
    1.1.0` and `bar 2.2.0`, your lower bounds does not actually make sense, as there is no way you
    can install `bar 2.1.0`. This function would relax your lower bounds to `foo>=1.0.0` and
    `bar>=2.1.0`.
    """
    return ConsistentLowerBoundsLazyRequirementSet(get_lazy_requirement_set(requirement_set))
