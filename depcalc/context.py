from __future__ import annotations

from abc import ABC, abstractmethod

from depcalc.release import ReleaseSet


class PackageContext(ABC):
    @property
    @abstractmethod
    def package(self) -> str:
        ...

    @abstractmethod
    def releases(self, package: str) -> ReleaseSet:
        ...


class Context(ABC):
    @abstractmethod
    def for_package(self, package: str) -> PackageContext:
        ...

    @abstractmethod
    def releases(self, package: str) -> ReleaseSet:
        ...
