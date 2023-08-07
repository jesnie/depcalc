from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import AbstractSet

from packaging.specifiers import Specifier
from packaging.version import Version


@dataclass(order=True, frozen=True)
class Release:
    package: str
    version: Version
    released_time: dt.datetime
    superseded_time: dt.datetime | None
    requires_python: AbstractSet[Specifier] = field(hash=False)


@dataclass(frozen=True)
class ReleaseSet:
    package: str
    releases: AbstractSet[Release]

    def __post_init__(self) -> None:
        assert all(
            r.package == self.package for r in self.releases
        ), f"Inconsistent package names in ReleaseSet. Found: {self}."
