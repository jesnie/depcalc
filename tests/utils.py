import datetime as dt
from typing import Collection

from packaging.version import Version

from depcalc.release import Release, ReleaseSet, infer_and_set_successor


def fake_release(
    *,
    package: str = "depcalc",
    version: str | Version = "1.2.3",
    released_time: dt.datetime = dt.datetime(2023, 8, 11, 12, 49),
    successor: Release | None = None,
) -> Release:
    if isinstance(version, str):
        version = Version(version)
    assert isinstance(version, Version)
    return Release(package, version, released_time, successor)


def fake_release_set(
    *,
    package: str = "depcalc",
    releases: Collection[str | Version | Release] = (),
    infer_successors: bool = True,
) -> ReleaseSet:
    releases_set = set()
    for r in releases:
        if not isinstance(r, Release):
            r = fake_release(package=package, version=r)
        assert isinstance(r, Release)
        releases_set.add(r)
    release_set = ReleaseSet(package, releases_set)
    if infer_successors:
        release_set = infer_and_set_successor(release_set)
    return release_set
