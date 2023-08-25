from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import Enum
from itertools import chain
from typing import Final, TypeAlias, Union, overload

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from compreq.contexts import Context, PackageContext
from compreq.releases import Release, ReleaseSet
from compreq.requirements import RequirementSet


class LazyRelease(ABC):
    """Strategy for computing a `Release` in the context of a package."""

    @abstractmethod
    def resolve(self, context: PackageContext) -> Release:
        """Compute the `Release`."""


@dataclass(order=True, frozen=True)
class EagerLazyRelease(LazyRelease):
    """`LazyRelease` that returns a given constant value."""

    release: Release

    def resolve(self, context: PackageContext) -> Release:
        return self.release


AnyRelease: TypeAlias = Release | LazyRelease
"""Type alias for anything that can be converted to a `LazyRelease`."""


def get_lazy_release(release: AnyRelease) -> LazyRelease:
    """Get a `LazyRelease` for the given release-like value."""
    if isinstance(release, Release):
        release = EagerLazyRelease(release)
    if isinstance(release, LazyRelease):
        return release
    raise AssertionError(f"Unknown type of release: {type(release)}")


class LazyReleaseSet(ABC):
    """Strategy for computing a `ReleaseSet` in the context of a package."""

    @abstractmethod
    def resolve(self, context: PackageContext) -> ReleaseSet:
        """Compute the `ReleaseSet`."""


@dataclass(order=True, frozen=True)
class EagerLazyReleaseSet(LazyReleaseSet):
    """`LazyReleaseSet` that returns a given constant set of (lazy) releases."""

    releases: frozenset[LazyRelease]

    def resolve(self, context: PackageContext) -> ReleaseSet:
        return ReleaseSet(
            context.package,
            frozenset(r.resolve(context) for r in self.releases),
        )


@dataclass(order=True, frozen=True)
class AllLazyReleaseSet(LazyReleaseSet):
    """`LazyReleaseSet` that returns all releases of a given package."""

    package: str | None
    """
    The package to get releases from. If `None`, the package of the context is used.
    """

    def resolve(self, context: PackageContext) -> ReleaseSet:
        package = self.package or context.package
        return context.releases(package)


@dataclass(order=True, frozen=True)
class ProdLazyReleaseSet(LazyReleaseSet):
    """
    `LazyReleaseSet` that filters another `LazyReleaseSet` and only returns the "production"
    releases.
    """

    source: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.source.resolve(context)
        return ReleaseSet(
            package=release_set.package,
            releases=frozenset(
                r for r in release_set if not (r.version.is_prerelease or r.version.is_devrelease)
            ),
        )


@dataclass(order=True, frozen=True)
class PreLazyReleaseSet(LazyReleaseSet):
    """
    `LazyReleaseSet` that filters another `LazyReleaseSet` and only returns the "production"
    and "pre-release" releases. (Not development releases.)
    """

    source: LazyReleaseSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.source.resolve(context)
        return ReleaseSet(
            package=release_set.package,
            releases=frozenset(r for r in release_set if not r.version.is_devrelease),
        )


@dataclass(order=True, frozen=True)
class SpecifierLazyReleaseSet(LazyReleaseSet):
    """
    `LazyReleaseSet` that filters another `LazyReleaseSet` based on specifiers.
    """

    source: LazyReleaseSet
    specifier_set: LazySpecifierSet

    def resolve(self, context: PackageContext) -> ReleaseSet:
        release_set = self.source.resolve(context)
        specifier_set = self.specifier_set.resolve(context)
        return ReleaseSet(
            package=release_set.package,
            releases=frozenset(r for r in release_set if r.version in specifier_set),
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
"""Type alias for anything that can be converted to a `LazyReleaseSet`."""


def get_lazy_release_set(release_set: AnyReleaseSet | None) -> LazyReleaseSet:
    """Get a `LazyRelease` for the given release-set-like value."""
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
        release_set = EagerLazyReleaseSet(frozenset([release_set]))
    if isinstance(release_set, ReleaseSet):
        release_set = EagerLazyReleaseSet(frozenset(get_lazy_release(r) for r in release_set))
    if isinstance(release_set, LazyReleaseSet):
        return release_set
    raise AssertionError(f"Unknown type of release set: {type(release_set)}")


class LazyVersion(ABC):
    """Strategy for computing a `Version` in the context of a package."""

    @abstractmethod
    def resolve(self, context: PackageContext) -> Version:
        """Compute the `Version`."""


@dataclass(order=True, frozen=True)
class EagerLazyVersion(LazyVersion):
    """`LazyVersion` that returns a given constant value."""

    version: Version

    def resolve(self, context: PackageContext) -> Version:
        return self.version


@dataclass(order=True, frozen=True)
class ReleaseLazyVersion(LazyVersion):
    """`LazyVersion` that gets the version from a `LazyRelease`."""

    release: LazyRelease

    def resolve(self, context: PackageContext) -> Version:
        return self.release.resolve(context).version


AnyVersion: TypeAlias = str | Release | LazyRelease | Version | LazyVersion
"""Type alias for anything that can be converted to a `LazyVersion`."""


def get_lazy_version(version: AnyVersion) -> LazyVersion:
    """Get a `LazyVersion` for the given version-like value."""
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
    """Enumeration of operators for specifiers."""

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
"""Type alias for anything that can be converted to a `SpecifierOperator`."""


def get_specifier_operator(op: AnySpecifierOperator) -> SpecifierOperator:
    """Get a `SpecifierOperator` for the given operator-like value."""
    if isinstance(op, str):
        return SpecifierOperator(op)
    if isinstance(op, SpecifierOperator):
        return op
    raise AssertionError(f"Unknown type of operator: {type(op)}")


@dataclass(order=True, frozen=True)
class LazySpecifier:
    """
    Strategy for computing a `Specifier` in the context of a package.

    Lazy specifiers can be combined with other specifiers; specifier-sets; and requiremnts using the
    `&` operator::

        lazy_specifier_set = lazy_specifier_1 & lazy_specifier_2
    """

    op: SpecifierOperator
    version: LazyVersion

    def resolve(self, context: PackageContext) -> Specifier:
        """Compute the `Specifier`."""
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
"""Type alias for anything that can be converted to a `LazySpecifier`."""


def get_lazy_specifier(specifier: AnySpecifier) -> LazySpecifier:
    """Get a `LazySpecifier` for the given specifier-like value."""
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
    """
    Strategy for computing a `SpecifierSet` in the context of a package.

    Lazy specifier-sets can be combined with specifiers; other specifier-sets; and requiremnts using
    the `&` operator::

        lazy_specifier_set = lazy_specifier_set_1 & lazy_specifier_set_2

    """

    specifiers: frozenset[LazySpecifier]

    def resolve(self, context: PackageContext) -> SpecifierSet:
        """Compute the `SpecifierSet`."""
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
"""Type alias for anything that can be converted to a `LazySpecifierSet`."""


def get_lazy_specifier_set(specifier_set: AnySpecifierSet) -> LazySpecifierSet:
    """Get a `LazySpecifierSet` for the given specifier-set-like value."""
    if isinstance(specifier_set, str):
        specifier_set = SpecifierSet(specifier_set)
    if isinstance(specifier_set, Specifier):
        specifier_set = get_lazy_specifier(specifier_set)
    if isinstance(specifier_set, LazySpecifier):
        specifier_set = LazySpecifierSet(frozenset([specifier_set]))
    if isinstance(specifier_set, SpecifierSet):
        specifier_set = LazySpecifierSet(frozenset(get_lazy_specifier(s) for s in specifier_set))
    if isinstance(specifier_set, LazySpecifierSet):
        return specifier_set
    raise AssertionError(f"Unknown type of specifier set: {type(specifier_set)}")


AnyMarker: TypeAlias = str | Marker
"""Type alias for anything that can be converted to a `Marker`."""


def get_marker(marker: AnyMarker) -> Marker:
    """Get a `Marker` for the given marker-like value."""
    if isinstance(marker, str):
        marker = Marker(marker)
    if isinstance(marker, Marker):
        return marker
    raise AssertionError(f"Unknown type of marker: {type(marker)}")


@dataclass(order=True, frozen=True)
class LazyRequirement:
    """
    Strategy for computing a `Requirement` in a context.

    A `LazyRequirement` can be in a partially configured state. To be valid a `LazyRequirement`
    must:

    * Have a `package` configured.
    * Cannot have both a `url` and a `specifier`.

    Lazy requiremnts can be combined with specifiers; specifier-sets; and other requiremnts using
    the `&` operator::

        lazy_requirement = lazy_requirement_1 & lazy_requirement_2
    """

    package: str | None
    """The required package. Required."""

    url: str | None
    """
    The url to download the package at. Use:

    * file:///... to refer to local files.
    * git+https://... to refer to git repositories.

    Mutually exclusive with `specifier`.
    """

    extras: frozenset[str]
    """Set of extras to install."""

    specifier: LazySpecifierSet
    """
    Specification of which versions of the package are valid.

    Mutually exclusize with `url`.
    """

    marker: Marker | None
    """Marker for specifying when this requirement should be used."""

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
        """Compute the `Requirement`."""
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


EMPTY_REQUIREMENT: Final[LazyRequirement] = LazyRequirement(
    package=None,
    url=None,
    extras=frozenset(),
    specifier=LazySpecifierSet(frozenset()),
    marker=None,
)
"""
A `LazyRequirement` without any values set.

Useful for constructing partial requirements::

    from dataclasses import replace

    replace(EMPTY_REQUIREMENT, package="foo.bar")

"""


AnyRequirement: TypeAlias = (
    str
    | Specifier
    | LazySpecifier
    | SpecifierSet
    | LazySpecifierSet
    | Requirement
    | LazyRequirement
)
"""Type alias for anything that can be converted to a `LazyRequirement`."""


def get_lazy_requirement(requirement: AnyRequirement) -> LazyRequirement:
    """Get a `LazyRequirement` for the given requirement-like value."""
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
            extras=frozenset(requirement.extras),
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
    """
    Combine two specifier-, specifier-set- or requirement-like values into a `LazySpecifierSet` or
    `LazyRequirement`.

    If either of the arguments are a requirement, the result is `LazyRequirement`. If neither
    argument is a requirement the result is a `LazySpecifierSet`.

    """
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
        extras = frozenset(chain(lhr.extras, rhr.extras))
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
        return LazySpecifierSet(frozenset(chain(lhss.specifiers, rhss.specifiers)))


@dataclass(order=True, frozen=True)
class LazyRequirementSet:
    """
    Strategy for computing a `RequirementSet` in a context.
    """

    requirements: frozenset[LazyRequirement]

    def resolve(self, context: Context) -> RequirementSet:
        """Compute the `RequirementSet`."""
        return RequirementSet.new(r.resolve(context) for r in self.requirements)


AnyRequirementSet: TypeAlias = (
    str
    | Specifier
    | LazySpecifier
    | SpecifierSet
    | LazySpecifierSet
    | Requirement
    | LazyRequirement
    | Mapping[str, AnyRequirement]
    | Iterable[AnyRequirement]
    | RequirementSet
    | LazyRequirementSet
)
"""Type alias for anything that can be converted to a `LazyRequirementSet`."""


def get_lazy_requirement_set(requirement_set: AnyRequirementSet) -> LazyRequirementSet:
    """Get a `LazyRequirementSet` for the given requirement-set-like value."""
    if isinstance(
        requirement_set,
        (str, Specifier, LazySpecifier, SpecifierSet, LazySpecifierSet, Requirement),
    ):
        requirement_set = get_lazy_requirement(requirement_set)
    if isinstance(requirement_set, LazyRequirement):
        requirement_set = LazyRequirementSet(frozenset([requirement_set]))
    if isinstance(requirement_set, Mapping):
        requirement_set = requirement_set.values()
    if isinstance(requirement_set, Iterable):
        requirement_set = LazyRequirementSet(
            frozenset(get_lazy_requirement(r) for r in requirement_set)
        )
    if isinstance(requirement_set, LazyRequirementSet):
        return requirement_set
    raise AssertionError(f"Unknown type of requirement set: {type(requirement_set)}")
