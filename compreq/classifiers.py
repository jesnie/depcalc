from typing import Sequence

from compreq.lazy import AnyReleaseSet
from compreq.roots import CompReq


def get_python_classifiers(cr: CompReq, python_releases: AnyReleaseSet) -> list[str]:
    version_strs_set = set()
    version_strs_list = []

    def add_version_str(s: str) -> None:
        if s in version_strs_set:
            return
        version_strs_set.add(s)
        version_strs_list.append(s)

    for release in sorted(cr.resolve_release_set("python", python_releases).releases):
        v = release.version
        add_version_str(f"{v.major}")
        add_version_str(f"{v.major}.{v.minor}")

    return [f"Programming Language :: Python :: {version_str}" for version_str in version_strs_list]


def set_python_classifiers(
    cr: CompReq,
    python_releases: AnyReleaseSet,
    classifiers: Sequence[str],
) -> Sequence[str]:
    classifiers = [c for c in classifiers if not c.startswith("Programming Language :: Python :: ")]
    classifiers += get_python_classifiers(cr, python_releases)
    return classifiers
