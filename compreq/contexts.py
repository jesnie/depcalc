from __future__ import annotations

from abc import ABC, abstractmethod

from packaging.specifiers import SpecifierSet

from compreq.pypireleases import get_pypi_releases
from compreq.pythonreleases import get_python_releases
from compreq.releases import ReleaseSet
from compreq.time import UtcDatetime, is_utc_datetime, utc_now


class PackageContext(ABC):
    """
    A context for resolving values related to a given package.
    """

    @property
    @abstractmethod
    def package(self) -> str:
        """The package values should be resolved relative to."""

    @property
    @abstractmethod
    def now(self) -> UtcDatetime:
        """The "current" time."""

    @abstractmethod
    def releases(self, package: str) -> ReleaseSet:
        """Fetch all releases of `package`."""


class Context(ABC):
    @property
    @abstractmethod
    def now(self) -> UtcDatetime:
        """The "current" time."""

    @abstractmethod
    def for_package(self, package: str) -> PackageContext:
        """Create a new context for the given package."""

    @abstractmethod
    def releases(self, package: str) -> ReleaseSet:
        """Fetch all releases of `package`."""


class DefaultPackageContext(PackageContext):
    """Default implementation of `PackageContext`."""

    def __init__(self, parent: Context, package: str) -> None:
        self._parent = parent
        self._package = package

    @property
    def package(self) -> str:
        return self._package

    @property
    def now(self) -> UtcDatetime:
        return self._parent.now

    def releases(self, package: str) -> ReleaseSet:
        return self._parent.releases(package)


class DefaultContext(Context):
    """Default implementation of `Context`."""

    def __init__(
        self, python_specifier: SpecifierSet | str, now: UtcDatetime | None = None
    ) -> None:
        if isinstance(python_specifier, str):
            python_specifier = SpecifierSet(python_specifier)
        assert isinstance(python_specifier, SpecifierSet)
        self._python_specifier = python_specifier

        if now is None:
            now = utc_now()
        assert is_utc_datetime(now)
        self._now = now

    @property
    def now(self) -> UtcDatetime:
        return self._now

    def for_package(self, package: str) -> DefaultPackageContext:
        return DefaultPackageContext(self, package)

    def releases(self, package: str) -> ReleaseSet:
        if package == "python":
            return get_python_releases(self._python_specifier)
        else:
            return get_pypi_releases(package)
