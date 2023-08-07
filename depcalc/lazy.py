from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from itertools import chain
from typing import AbstractSet, TypeAlias

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from depcalc.context import Context, PackageContext
from depcalc.release import Release, ReleaseSet


class LazyRelease(ABC):
    @abstractmethod
    def resolve(self, context: PackageContext) -> Release:
        ...


AnyRelease: TypeAlias = Release | LazyRelease


def get_lazy_release(release: AnyRelease) -> LazyRelease:
    if isinstance(release, Release):
        release = EagerLazyRelease(release)
    if isinstance(release, LazyRelease):
        return release
    raise AssertionError(f"Unknown type of release: {type(release)}")


@dataclass(order=True, frozen=True)
class EagerLazyRelease(LazyRelease):
    release: Release

    def resolve(self, context: PackageContext) -> Release:
        return self.release


class LazyReleaseSet(ABC):
    @abstractmethod
    def resolve(self, context: PackageContext) -> ReleaseSet:
        ...


@dataclass(order=True, frozen=True)
class EagerLazyReleaseSet(LazyReleaseSet):
    releases: AbstractSet[LazyRelease]

    def resolve(self, context: PackageContext) -> ReleaseSet:
        return ReleaseSet(
            context.package,
            {r.resolve(context) for r in self.releases},
        )


AnyReleaseSet: TypeAlias = AnyRelease | ReleaseSet | LazyReleaseSet


def get_lazy_release_set(release_set: AnyReleaseSet) -> LazyReleaseSet:
    if isinstance(release_set, Release):
        release_set = EagerLazyRelease(release_set)
    if isinstance(release_set, LazyRelease):
        release_set = EagerLazyReleaseSet({release_set})
    if isinstance(release_set, ReleaseSet):
        release_set = EagerLazyReleaseSet({get_lazy_release(r) for r in release_set.releases})
    if isinstance(release_set, LazyReleaseSet):
        return release_set
    raise AssertionError(f"Unknown type of release set: {type(release_set)}")


class LazyVersion(ABC):
    @abstractmethod
    def resolve(self, context: PackageContext) -> Version:
        ...


@dataclass(order=True, frozen=True)
class EagerLazyVersion(LazyVersion):
    version: Version

    def resolve(self, context: PackageContext) -> Version:
        return self.version


@dataclass(order=True, frozen=True)
class ReleaseLazyVersion(LazyVersion):
    release: LazyRelease

    def resolve(self, context: PackageContext) -> Version:
        return self.release.resolve(context).version


AnyVersion: TypeAlias = str | Release | LazyRelease | Version | LazyVersion


def get_lazy_version(version: AnyVersion) -> LazyVersion:
    if isinstance(version, str):
        version = Version(version)
    if isinstance(version, Release):
        version = version.version
    if isinstance(version, LazyRelease):
        version = ReleaseLazyVersion(version)
    if isinstance(version, Version):
        version = EagerLazyVersion(version)
    if isinstance(version, LazyVersion):
        return version
    raise AssertionError(f"Unknown type of version: {type(version)}")


class SpecifierOperator(Enum):
    COMPATIBLE = "~="
    NE = "!="
    EQ = "=="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    ARBITRARY_EQ = "==="


AnySpecifierOperator: TypeAlias = str | SpecifierOperator


def get_specifier_operator(op: AnySpecifierOperator) -> SpecifierOperator:
    if isinstance(op, str):
        return SpecifierOperator(op)
    if isinstance(op, SpecifierOperator):
        return op
    raise AssertionError(f"Unknown type of operator: {type(op)}")


@dataclass(order=True, frozen=True)
class LazySpecifier:
    op: SpecifierOperator
    version: LazyVersion

    def resolve(self, context: PackageContext) -> Specifier:
        op = self.op
        version = self.version.resolve(context)
        return Specifier(f"{op.value}{version}")

    def __and__(self, rhs: AnyRequirement) -> LazyRequirement:
        return LazyRequirement.compose(self, rhs)

    def __rand__(self, lhs: AnyRequirement) -> LazyRequirement:
        return LazyRequirement.compose(lhs, self)


AnySpecifier: TypeAlias = str | Specifier | LazySpecifier


def get_lazy_specifier(specifier: AnySpecifier) -> LazySpecifier:
    if isinstance(specifier, str):
        specifier = Specifier(specifier)
    if isinstance(specifier, Specifier):
        op = get_specifier_operator(specifier.operator)
        version = get_lazy_version(specifier.version)
        specifier = LazySpecifier(op, version)
    if isinstance(specifier, LazySpecifier):
        return specifier
    raise AssertionError(f"Unknown type of specifier: {type(specifier)}")


AnyMarker: TypeAlias = str | Marker


def get_marker(marker: AnyMarker) -> Marker:
    if isinstance(marker, str):
        marker = Marker(marker)
    if isinstance(marker, Marker):
        return marker
    raise AssertionError(f"Unknown type of marker: {type(marker)}")


@dataclass(order=True, frozen=True)
class LazyRequirement:
    package: str | None
    url: str | None
    extras: AbstractSet[str]
    specifier: AbstractSet[LazySpecifier]
    marker: Marker | None

    def __post_init__(self) -> None:
        assert (self.url is None) or not self.specifier, (
            "A requirement cannot have both a url and a specifier."
            f" Found: {self.url}, {self.specifier}."
        )

    @staticmethod
    def compose(lhs: AnyRequirement, rhs: AnyRequirement) -> LazyRequirement:
        lhr = get_lazy_requirement(lhs)
        rhr = get_lazy_requirement(rhs)

        assert lhr.package is None or rhr.package is None or lhr.package == rhr.package, (
            "A requirement can have at most one package name."
            f" Found: {lhr.package} and {rhr.package}."
        )
        assert (
            lhr.url is None or rhr.url is None or lhr.url == rhr.url
        ), f"A requirement can have at most one url. Found: {lhr.url} and {rhr.url}."
        package = lhr.package or rhr.package
        url = lhr.url or rhr.url
        extras = set(chain(lhr.extras, rhr.extras))
        specifier = set(chain(lhr.specifier, rhr.specifier))
        marker: Marker | None
        if lhr.marker is None:
            marker = rhr.marker
        elif rhr.marker is None:
            marker = lhr.marker
        elif lhr.marker == rhr.marker:
            marker = lhr.marker
        else:
            marker = Marker(f"({lhr.marker}) and ({rhr.marker})")
        return LazyRequirement(
            package=package,
            url=url,
            extras=extras,
            specifier=specifier,
            marker=marker,
        )

    def __and__(self, rhs: AnyRequirement) -> LazyRequirement:
        return LazyRequirement.compose(self, rhs)

    def __rand__(self, lhs: AnyRequirement) -> LazyRequirement:
        return LazyRequirement.compose(lhs, self)

    def assert_valid(self) -> None:
        assert self.package, f"A requirement must have the package name set. Found: {self.package}."

    def resolve(self, context: Context) -> Requirement:
        self.assert_valid()
        assert self.package

        tokens = []
        tokens.append(self.package)

        if self.extras:
            formatted_extras = ",".join(sorted(self.extras))
            tokens.append(f"[{formatted_extras}]")

        package_context = context.for_package(self.package)
        specifiers = [s.resolve(package_context) for s in sorted(self.specifier)]
        tokens.append(",".join(str(s) for s in specifiers))

        if self.url:
            tokens.append(f"@ {self.url}")
            if self.marker:
                tokens.append(" ")

        if self.marker:
            tokens.append(f"; {self.marker}")

        return Requirement("".join(tokens))


AnyRequirement: TypeAlias = (
    str | Specifier | SpecifierSet | LazySpecifier | Requirement | LazyRequirement
)


def get_lazy_requirement(requirement: AnyRequirement) -> LazyRequirement:
    if isinstance(requirement, str):
        requirement = Requirement(requirement)
    if isinstance(requirement, Specifier):
        requirement = get_lazy_specifier(requirement)
    if isinstance(requirement, LazySpecifier):
        requirement = LazyRequirement(
            package=None,
            url=None,
            extras=set(),
            specifier={requirement},
            marker=None,
        )
    if isinstance(requirement, SpecifierSet):
        requirement = LazyRequirement(
            package=None,
            url=None,
            extras=set(),
            specifier={get_lazy_specifier(s) for s in requirement},
            marker=None,
        )
    if isinstance(requirement, Requirement):
        requirement = LazyRequirement(
            package=requirement.name,
            url=requirement.url,
            extras=requirement.extras,
            specifier={get_lazy_specifier(s) for s in requirement.specifier},
            marker=requirement.marker,
        )
    if isinstance(requirement, LazyRequirement):
        return requirement
    raise AssertionError(f"Unknown type of requirement: {type(requirement)}")
