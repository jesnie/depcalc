from __future__ import annotations

from abc import ABC, abstractmethod

from packaging.specifiers import SpecifierSet

from compreq.pypireleases import get_pypi_releases
from compreq.pythonreleases import get_python_releases
from compreq.release import ReleaseSet
from compreq.time import UtcDatetime, is_utc_datetime, utc_now


class PackageContext(ABC):
    @property
    @abstractmethod
    def package(self) -> str:
        ...

    @property
    @abstractmethod
    def now(self) -> UtcDatetime:
        ...

    @abstractmethod
    def releases(self, package: str) -> ReleaseSet:
        ...


class Context(ABC):
    @property
    @abstractmethod
    def now(self) -> UtcDatetime:
        ...

    @abstractmethod
    def for_package(self, package: str) -> PackageContext:
        ...

    @abstractmethod
    def releases(self, package: str) -> ReleaseSet:
        ...


class DefaultPackageContext(PackageContext):
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
