from __future__ import annotations

from dataclasses import dataclass, replace
from typing import AbstractSet, Collection

from packaging.version import Version

from compreq.time import UtcDatetime


@dataclass(order=True, frozen=True)
class Release:
    package: str
    version: Version
    released_time: UtcDatetime
    successor: Release | None


@dataclass(frozen=True)
class ReleaseSet:
    package: str
    releases: AbstractSet[Release]

    def __post_init__(self) -> None:
        assert all(
            r.package == self.package for r in self.releases
        ), f"Inconsistent package names in ReleaseSet. Found: {self}."


def infer_successor(versions: Collection[Version]) -> dict[Version, Version | None]:
    next_main: Version | None = None
    next_pre: Version | None = None
    next_dev: Version | None = None
    result = {}
    for version in sorted(versions, reverse=True):
        if version.is_devrelease:
            result[version] = next_dev
            next_dev = version
        elif version.is_prerelease:
            result[version] = next_pre
            next_dev = next_pre = version
        else:
            result[version] = next_main
            next_main = next_pre = next_dev = version
    return result


def infer_and_set_successor(releases: ReleaseSet) -> ReleaseSet:
    by_version = {r.version: r for r in releases.releases}
    successors = infer_successor(by_version)
    for r in sorted(releases.releases, reverse=True):
        s = successors.get(r.version)
        if s is not None:
            r = replace(r, successor=by_version[s])
        by_version[r.version] = r
    return ReleaseSet(package=releases.package, releases=set(by_version.values()))
