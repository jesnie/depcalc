from dataclasses import replace

from compreq.lazy import (
    EMPTY_REQUIREMENT,
    AllLazyReleaseSet,
    AnyMarker,
    AnySpecifier,
    AnySpecifierSet,
    LazyReleaseSet,
    LazyRequirement,
    LazySpecifier,
    LazySpecifierSet,
    PreLazyReleaseSet,
    ProdLazyReleaseSet,
    get_lazy_specifier,
    get_lazy_specifier_set,
    get_marker,
)
from compreq.versiontoken import VersionToken

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


def releases(package: str | None = None) -> LazyReleaseSet:  # pylint: disable=redefined-outer-name
    return ProdLazyReleaseSet(AllLazyReleaseSet(package))


def prereleases(
    package: str | None = None,  # pylint: disable=redefined-outer-name
) -> LazyReleaseSet:
    return PreLazyReleaseSet(AllLazyReleaseSet(package))


def devreleases(
    package: str | None = None,  # pylint: disable=redefined-outer-name
) -> LazyReleaseSet:
    return AllLazyReleaseSet(package)
