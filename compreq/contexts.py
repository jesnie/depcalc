from __future__ import annotations

from abc import ABC, abstractmethod

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from compreq.bounds import get_bounds
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
    def default_python(self) -> Version:
        """Which version of Python to use while computing requirements."""

    @property
    @abstractmethod
    def python_specifier(self) -> SpecifierSet:
        """Which versions of Python are allowed."""

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
    def default_python(self) -> Version:
        """Which version of Python to use while computing requirements."""

    @property
    @abstractmethod
    def python_specifier(self) -> SpecifierSet:
        """Which versions of Python are allowed."""

    @property
    @abstractmethod
    def now(self) -> UtcDatetime:
        """The "current" time."""

    @abstractmethod
    def for_python(
        self, python_specifier: SpecifierSet | str, *, default_python: Version | str | None = None
    ) -> Context:
        """
        Create a new context, for the given versions of Python.

        If `default_python` is `None`, the lower bound on `python_specifier` is used.
        """

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
    def default_python(self) -> Version:
        return self._parent.default_python

    @property
    def python_specifier(self) -> SpecifierSet:
        return self._parent.python_specifier

    @property
    def now(self) -> UtcDatetime:
        return self._parent.now

    def releases(self, package: str) -> ReleaseSet:
        return self._parent.releases(package)


class DefaultContext(Context):
    """Default implementation of `Context`."""

    def __init__(
        self,
        python_specifier: SpecifierSet | str,
        *,
        default_python: Version | str | None = None,
        now: UtcDatetime | None = None,
    ) -> None:
        if isinstance(python_specifier, str):
            python_specifier = SpecifierSet(python_specifier)
        assert isinstance(python_specifier, SpecifierSet)
        self._python_specifier = python_specifier

        if isinstance(default_python, str):
            default_python = Version(default_python)
        elif default_python is None:
            bounds = get_bounds(python_specifier)
            assert bounds.lower and bounds.lower_inclusive, (
                "Can only infer a `default_python` when `python_specifier` has an inclusive lower"
                " bound."
                f" Found: {python_specifier=}"
            )
            default_python = bounds.lower
        assert isinstance(default_python, Version)
        self._default_python = default_python

        if now is None:
            now = utc_now()
        assert is_utc_datetime(now)
        self._now = now

    @property
    def default_python(self) -> Version:
        return self._default_python

    @property
    def python_specifier(self) -> SpecifierSet:
        return self._python_specifier

    @property
    def now(self) -> UtcDatetime:
        return self._now

    def for_python(
        self, python_specifier: SpecifierSet | str, *, default_python: Version | str | None = None
    ) -> Context:
        return DefaultContext(
            python_specifier=python_specifier, default_python=default_python, now=self._now
        )

    def for_package(self, package: str) -> DefaultPackageContext:
        return DefaultPackageContext(self, package)

    def releases(self, package: str) -> ReleaseSet:
        if package == "python":
            return get_python_releases(self._python_specifier)
        else:
            return get_pypi_releases(package)
