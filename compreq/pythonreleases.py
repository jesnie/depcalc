import re
from functools import cache

from packaging.specifiers import SpecifierSet
from packaging.version import VERSION_PATTERN, Version, parse

from compreq.pythonftp import ROOT
from compreq.releases import Release, ReleaseSet, infer_and_set_successor

RELEASE_DIR_RE = re.compile(r"(" + VERSION_PATTERN + r")/", re.VERBOSE | re.IGNORECASE)
VERSION_TGZ_RE = re.compile(r"Python-(" + VERSION_PATTERN + r").tgz", re.VERBOSE | re.IGNORECASE)


@cache
def get_python_releases(python_specifiers: SpecifierSet) -> ReleaseSet:
    """
    Get all releases of Python.

    The `python_specifiers` argument is used to pre-filter the Python versions to fetch. This
    function can be a bit slow, and setting a tight pre-filter can significantly speed it up. If you
    *really* want to fetch *all* Python releases use `get_python_releases(SpecifierSet())`.
    """

    assert not any(
        Version(s.version).is_prerelease or Version(s.version).is_devrelease
        for s in python_specifiers
    ), (
        "Initial Python filter specifiers do not supper pre- or dev releases."
        f" Found: {python_specifiers}."
    )
    python = ROOT.ls()["python/"].as_dir()

    result: set[Release] = set()
    for release, release_dir in python.ls().items():
        match = RELEASE_DIR_RE.fullmatch(release)
        if match is None:
            continue

        version = parse(match[1])
        if version not in python_specifiers:
            continue

        for name, path in release_dir.as_dir().ls().items():
            match = VERSION_TGZ_RE.fullmatch(name)
            if match is None:
                continue

            result.add(
                Release(
                    package="python",
                    version=parse(match[1]),
                    released_time=path.modified,
                    successor=None,  # Set by infer_and_set_successor
                )
            )

    return infer_and_set_successor(ReleaseSet("python", frozenset(result)))
