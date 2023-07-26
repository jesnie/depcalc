from packaging.requirements import Requirement
from packaging.specifiers import Specifier
from packaging.version import Version

from depcalc.context import Context, DefaultContext
from depcalc.lazy import (
    AnyRelease,
    AnyReleaseSet,
    AnyRequirement,
    AnySpecifier,
    AnyVersion,
    get_lazy_release,
    get_lazy_release_set,
    get_lazy_requirement,
    get_lazy_specifier,
    get_lazy_version,
)
from depcalc.release import Release, ReleaseSet


class DepCalc:
    def __init__(self, context: Context | None = None) -> None:
        if context is None:
            context = DefaultContext()
        assert context is not None
        self._context = context

    def resolve_release(self, package: str, release: AnyRelease) -> Release:
        context = self._context.for_package(package)
        return get_lazy_release(release).resolve(context)

    def resolve_release_set(self, package: str, release_set: AnyReleaseSet) -> ReleaseSet:
        context = self._context.for_package(package)
        return get_lazy_release_set(release_set).resolve(context)

    def resolve_version(self, package: str, version: AnyVersion) -> Version:
        context = self._context.for_package(package)
        return get_lazy_version(version).resolve(context)

    def resolve_specifier(self, package: str, specifier: AnySpecifier) -> Specifier:
        context = self._context.for_package(package)
        return get_lazy_specifier(specifier).resolve(context)

    def resolve_requirement(self, requirement: AnyRequirement) -> Requirement:
        return get_lazy_requirement(requirement).resolve(self._context)
