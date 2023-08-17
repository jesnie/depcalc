from typing import NoReturn, overload

from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from compreq.context import Context, DefaultContext
from compreq.lazy import (
    AnyRelease,
    AnyReleaseSet,
    AnyRequirement,
    AnySpecifier,
    AnySpecifierSet,
    AnyVersion,
    get_lazy_release,
    get_lazy_release_set,
    get_lazy_requirement,
    get_lazy_specifier,
    get_lazy_specifier_set,
    get_lazy_version,
)
from compreq.release import Release, ReleaseSet


class CompReq:
    @overload
    def __init__(self, context: None = None, *, python_specifier: None = None) -> NoReturn:
        ...

    @overload
    def __init__(self, context: None = None, *, python_specifier: SpecifierSet | str) -> None:
        ...

    @overload
    def __init__(self, context: Context, *, python_specifier: None = None) -> None:
        ...

    @overload
    def __init__(self, context: Context, *, python_specifier: SpecifierSet | str) -> NoReturn:
        ...

    def __init__(
        self, context: Context | None = None, *, python_specifier: SpecifierSet | str | None = None
    ) -> None:
        assert (context is None) != (python_specifier is None), (
            "Must set exactly one of `context` and `python_specifier`."
            f" Found: {context=}, {python_specifier=}"
        )
        if context is None:
            assert python_specifier is not None, python_specifier
            context = DefaultContext(python_specifier)
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

    def resolve_specifier_set(self, package: str, specifier_set: AnySpecifierSet) -> SpecifierSet:
        context = self._context.for_package(package)
        return get_lazy_specifier_set(specifier_set).resolve(context)

    def resolve_requirement(self, requirement: AnyRequirement) -> Requirement:
        return get_lazy_requirement(requirement).resolve(self._context)
