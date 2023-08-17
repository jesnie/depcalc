import datetime as dt
from typing import Collection

from packaging.version import Version

from compreq.release import Release, ReleaseSet, infer_and_set_successor
from compreq.time import UtcDatetime, is_utc_datetime


def utc(time: dt.datetime) -> UtcDatetime:
    if not is_utc_datetime(time):
        time = time.replace(tzinfo=dt.timezone.utc)
    assert is_utc_datetime(time)
    return time


def fake_release(
    *,
    package: str = "compreq",
    version: str | Version = "1.2.3",
    released_time: dt.datetime = dt.datetime(2023, 8, 11, 12, 49),
    successor: Release | None = None,
) -> Release:
    if isinstance(version, str):
        version = Version(version)
    assert isinstance(version, Version)
    return Release(package, version, utc(released_time), successor)


def fake_release_set(
    *,
    package: str = "compreq",
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
