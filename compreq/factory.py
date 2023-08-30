from typing import NewType

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

_Unset = NewType("_Unset", object)
_UNSET = _Unset(object())


def make_requirement(
    base: Requirement | _Unset = _UNSET,
    *,
    package: str | _Unset = _UNSET,
    url: str | None | _Unset = _UNSET,
    extras: set[str] | _Unset = _UNSET,
    specifier: SpecifierSet | _Unset = _UNSET,
    marker: Marker | None | _Unset = _UNSET,
) -> Requirement:
    result = Requirement.__new__(Requirement)

    if isinstance(package, str):
        result.name = package
    else:
        assert isinstance(base, Requirement)
        result.name = base.name

    if (url is None) or isinstance(url, str):
        result.url = url
    elif isinstance(base, Requirement):
        result.url = base.url
    else:
        result.url = None

    if isinstance(extras, set):
        result.extras = extras
    elif isinstance(base, Requirement):
        result.extras = base.extras
    else:
        result.extras = set()

    if isinstance(specifier, SpecifierSet):
        result.specifier = specifier
    elif isinstance(base, Requirement):
        result.specifier = base.specifier
    else:
        result.specifier = SpecifierSet()

    if (marker is None) or isinstance(marker, Marker):
        result.marker = marker
    elif isinstance(base, Requirement):
        result.marker = base.marker
    else:
        result.marker = None

    return result
