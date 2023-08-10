from depcalc.lazy import (
    AnyMarker,
    AnySpecifier,
    LazyReleaseSet,
    LazyRequirement,
    RawLazyReleaseSet,
    get_lazy_specifier,
    get_marker,
)
from depcalc.versiontoken import VersionToken

version = VersionToken()
v = version


def package(value: str) -> LazyRequirement:
    return LazyRequirement(
        package=value,
        url=None,
        extras=set(),
        specifier=set(),
        marker=None,
    )


pkg = package


def url(value: str) -> LazyRequirement:
    return LazyRequirement(
        package=None,
        url=value,
        extras=set(),
        specifier=set(),
        marker=None,
    )


def extra(value: str) -> LazyRequirement:
    return LazyRequirement(
        package=None,
        url=None,
        extras={value},
        specifier=set(),
        marker=None,
    )


def specifier(value: AnySpecifier) -> LazyRequirement:
    return LazyRequirement(
        package=None,
        url=None,
        extras=set(),
        specifier={get_lazy_specifier(value)},
        marker=None,
    )


def marker(value: AnyMarker) -> LazyRequirement:
    return LazyRequirement(
        package=None,
        url=None,
        extras=set(),
        specifier=set(),
        marker=get_marker(value),
    )


def releases(package: str | None = None) -> LazyReleaseSet:  # pylint: disable=redefined-outer-name
    return RawLazyReleaseSet(package)
