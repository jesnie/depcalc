from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import Enum
from itertools import chain
from typing import AbstractSet, TypeAlias, Union, overload

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from compreq.context import Context, PackageContext
from compreq.release import Release, ReleaseSet


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


@dataclass(order=True, frozen=True)
class AllLazyReleaseSet(LazyReleaseSet):
    package: str | None

    def resolve(self, context: PackageContext) -> ReleaseSet:
        package = self.package or context.package
        return context.releases(package)


@dataclass(order=True, frozen=True)
class ProdLazyReleaseSet(LazyReleaseSet):
    source: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.source.resolve(context)
        return ReleaseSet(
            package=release_set.package,
            releases={
                r
                for r in release_set.releases
                if not (r.version.is_prerelease or r.version.is_devrelease)
            },
        )


@dataclass(order=True, frozen=True)
class PreLazyReleaseSet(LazyReleaseSet):
    source: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.source.resolve(context)
        return ReleaseSet(
            package=release_set.package,
            releases={r for r in release_set.releases if not r.version.is_devrelease},
        )


@dataclass(order=True, frozen=True)
class SpecifierLazyReleaseSet(LazyReleaseSet):
    source: LazyReleaseSet
    specifier_set: LazySpecifierSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.source.resolve(context)
        specifier_set = self.specifier_set.resolve(context)
        return ReleaseSet(
            package=release_set.package,
            releases={r for r in release_set.releases if r.version in specifier_set},
        )


AnyReleaseSet: TypeAlias = Union[
    None,
    str,
    Specifier,
    "LazySpecifier",
    SpecifierSet,
    "LazySpecifierSet",
    Requirement,
    "LazyRequirement",
    Release,
    LazyRelease,
    ReleaseSet,
    LazyReleaseSet,
]


def get_lazy_release_set(release_set: AnyReleaseSet | None) -> LazyReleaseSet:
    if release_set is None:
        release_set = ProdLazyReleaseSet(AllLazyReleaseSet(None))
    if isinstance(release_set, str):
        release_set = ProdLazyReleaseSet(AllLazyReleaseSet(release_set))
    if isinstance(release_set, (Specifier, LazySpecifier, SpecifierSet)):
        release_set = get_lazy_specifier_set(release_set)
    if isinstance(release_set, LazySpecifierSet):
        release_set = SpecifierLazyReleaseSet(
            ProdLazyReleaseSet(AllLazyReleaseSet(None)),
            release_set,
        )
    if isinstance(release_set, Requirement):
        release_set = get_lazy_requirement(release_set)
    if isinstance(release_set, LazyRequirement):
        release_set = SpecifierLazyReleaseSet(
            ProdLazyReleaseSet(AllLazyReleaseSet(release_set.package)), release_set.specifier
        )
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

    def __lt__(self, other: SpecifierOperator) -> bool:
        return self.value < other.value

    def __gt__(self, other: SpecifierOperator) -> bool:
        return self.value > other.value

    def __le__(self, other: SpecifierOperator) -> bool:
        return self.value <= other.value

    def __ge__(self, other: SpecifierOperator) -> bool:
        return self.value >= other.value


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

    @overload
    def __and__(self, rhs: AnySpecifierSet) -> LazySpecifierSet:
        ...

    @overload
    def __and__(self, rhs: Requirement | LazyRequirement) -> LazyRequirement:
        ...

    def __and__(self, rhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
        return compose(self, rhs)

    @overload
    def __rand__(self, lhs: AnySpecifierSet) -> LazySpecifierSet:
        ...

    @overload
    def __rand__(self, lhs: Requirement | LazyRequirement) -> LazyRequirement:
        ...

    def __rand__(self, lhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
        return compose(lhs, self)


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


@dataclass(frozen=True)
class LazySpecifierSet:
    specifiers: AbstractSet[LazySpecifier]

    def resolve(self, context: PackageContext) -> SpecifierSet:
        specifiers = [s.resolve(context) for s in self.specifiers]
        return SpecifierSet(",".join(str(s) for s in specifiers))

    @overload
    def __and__(self, rhs: AnySpecifierSet) -> LazySpecifierSet:
        ...

    @overload
    def __and__(self, rhs: Requirement | LazyRequirement) -> LazyRequirement:
        ...

    def __and__(self, rhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
        return compose(self, rhs)

    @overload
    def __rand__(self, lhs: AnySpecifierSet) -> LazySpecifierSet:
        ...

    @overload
    def __rand__(self, lhs: Requirement | LazyRequirement) -> LazyRequirement:
        ...

    def __rand__(self, lhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
        return compose(lhs, self)


AnySpecifierSet: TypeAlias = str | Specifier | LazySpecifier | SpecifierSet | LazySpecifierSet


def get_lazy_specifier_set(specifier_set: AnySpecifierSet) -> LazySpecifierSet:
    if isinstance(specifier_set, str):
        specifier_set = SpecifierSet(specifier_set)
    if isinstance(specifier_set, Specifier):
        specifier_set = get_lazy_specifier(specifier_set)
    if isinstance(specifier_set, LazySpecifier):
        specifier_set = LazySpecifierSet({specifier_set})
    if isinstance(specifier_set, SpecifierSet):
        specifier_set = LazySpecifierSet({get_lazy_specifier(s) for s in specifier_set})
    if isinstance(specifier_set, LazySpecifierSet):
        return specifier_set
    raise AssertionError(f"Unknown type of specifier set: {type(specifier_set)}")


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
    specifier: LazySpecifierSet
    marker: Marker | None

    def __post_init__(self) -> None:
        assert (self.url is None) or not self.specifier.specifiers, (
            "A requirement cannot have both a url and a specifier."
            f" Found: {self.url}, {self.specifier}."
        )

    def __and__(self, rhs: AnyRequirement) -> LazyRequirement:
        return compose(self, rhs)

    def __rand__(self, lhs: AnyRequirement) -> LazyRequirement:
        return compose(lhs, self)

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
        specifier = self.specifier.resolve(package_context)
        tokens.append(str(specifier))

        if self.url:
            tokens.append(f"@ {self.url}")
            if self.marker:
                tokens.append(" ")

        if self.marker:
            tokens.append(f"; {self.marker}")

        return Requirement("".join(tokens))


EMPTY_REQUIREMENT = LazyRequirement(
    package=None,
    url=None,
    extras=set(),
    specifier=LazySpecifierSet(set()),
    marker=None,
)


AnyRequirement: TypeAlias = (
    str
    | Specifier
    | LazySpecifier
    | SpecifierSet
    | LazySpecifierSet
    | Requirement
    | LazyRequirement
)


def get_lazy_requirement(requirement: AnyRequirement) -> LazyRequirement:
    if isinstance(requirement, str):
        requirement = Requirement(requirement)
    if isinstance(requirement, (Specifier, LazySpecifier, SpecifierSet)):
        requirement = get_lazy_specifier_set(requirement)
    if isinstance(requirement, LazySpecifierSet):
        requirement = replace(EMPTY_REQUIREMENT, specifier=requirement)
    if isinstance(requirement, Requirement):
        requirement = LazyRequirement(
            package=requirement.name,
            url=requirement.url,
            extras=requirement.extras,
            specifier=get_lazy_specifier_set(requirement.specifier),
            marker=requirement.marker,
        )
    if isinstance(requirement, LazyRequirement):
        return requirement
    raise AssertionError(f"Unknown type of requirement: {type(requirement)}")


@overload
def compose(lhs: AnySpecifierSet, rhs: AnySpecifierSet) -> LazySpecifierSet:
    ...


@overload
def compose(lhs: AnyRequirement, rhs: Requirement | LazyRequirement) -> LazyRequirement:
    ...


@overload
def compose(lhs: Requirement | LazyRequirement, rhs: AnyRequirement) -> LazyRequirement:
    ...


def compose(lhs: AnyRequirement, rhs: AnyRequirement) -> LazySpecifierSet | LazyRequirement:
    if isinstance(lhs, (Requirement, LazyRequirement)) or isinstance(
        rhs, (Requirement, LazyRequirement)
    ):
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
        specifier = compose(lhr.specifier, rhr.specifier)
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
    else:
        lhss = get_lazy_specifier_set(lhs)
        rhss = get_lazy_specifier_set(rhs)
        return LazySpecifierSet(set(chain(lhss.specifiers, rhss.specifiers)))
