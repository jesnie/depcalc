import datetime as dt
from functools import cache

import requests
from dateutil.parser import isoparse
from packaging.version import parse

from depcalc.release import Release, ReleaseSet, infer_and_set_successor


@cache
def get_pypi_releases(package: str) -> ReleaseSet:
    url = f"https://pypi.org/pypi/{package}/json"
    data = requests.get(url, timeout=600.0).json()
    result = set()
    for release, release_data in data["releases"].items():
        version = parse(release)
        released_time: dt.datetime | None = None

        for file_data in release_data:
            file_yanked = file_data["yanked"]
            if file_yanked:
                continue

            file_released_time = isoparse(file_data["upload_time_iso_8601"])
            if released_time is None:
                released_time = file_released_time
            else:
                released_time = max(released_time, file_released_time)

        if released_time is None:
            continue

        result.add(
            Release(
                package=package,
                version=version,
                released_time=released_time,
                successor=None,  # Set by infer_and_set_successor.
            )
        )

    return infer_and_set_successor(ReleaseSet(package, result))


def main() -> None:
    for v in sorted(get_pypi_releases("tensorflow").releases):
        print(v)


if __name__ == "__main__":
    main()
