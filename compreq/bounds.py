from dataclasses import dataclass
from typing import AbstractSet

from packaging.specifiers import SpecifierSet
from packaging.version import Version

import compreq.operators as o
from compreq.levels import IntLevel


@dataclass(order=True, frozen=True)
class Bounds:
    specifier_set: SpecifierSet
    upper: Version | None
    upper_inclusive: bool
    lower: Version | None
    lower_inclusive: bool
    exclusions: AbstractSet[Version]

    def minimal_specifier_set(self, exclusions: bool = True) -> SpecifierSet:
        return self.upper_specifier_set(False) & self.lower_specifier_set(exclusions)

    def upper_specifier_set(self, exclusions: bool = True) -> SpecifierSet:
        result = SpecifierSet()
        if self.upper is not None:
            if self.upper_inclusive:
                result &= SpecifierSet(f"<={str(self.upper)}")
            else:
                result &= SpecifierSet(f"<{str(self.upper)}")
        if exclusions:
            result &= self.exclusions_specifier_set()
        return result

    def lower_specifier_set(self, exclusions: bool = True) -> SpecifierSet:
        result = SpecifierSet()
        if self.lower is not None:
            if self.lower_inclusive:
                result &= SpecifierSet(f">={str(self.lower)}")
            else:
                result &= SpecifierSet(f">{str(self.lower)}")
        if exclusions:
            result &= self.exclusions_specifier_set()
        return result

    def exclusions_specifier_set(self) -> SpecifierSet:
        return SpecifierSet(",".join(f"!={str(v)}" for v in self.exclusions))


def get_bounds(specifier_set: SpecifierSet) -> Bounds:
    upper: Version | None = None
    upper_inclusive: bool = False
    lower: Version | None = None
    lower_inclusive: bool = False
    exclusions: set[Version] = set()
    for specifier in specifier_set:
        version = Version(specifier.version)
        match (specifier.operator):
            case ">":
                if lower is None or version >= lower:
                    lower = version
                    lower_inclusive = False
            case ">=":
                if lower is None or version > lower:
                    lower = version
                    lower_inclusive = True
            case "<":
                if upper is None or version <= upper:
                    upper = version
                    upper_inclusive = False
            case "<=":
                if upper is None or version < upper:
                    upper = version
                    upper_inclusive = True
            case "==":
                if lower is None or version > lower:
                    lower = version
                    lower_inclusive = True
                if upper is None or version < upper:
                    upper = version
                    upper_inclusive = True
            case "~=":
                vupper = o.CeilLazyVersion.ceil(IntLevel(-1), version, keep_trailing_zeros=False)
                if upper is None or vupper <= upper:
                    upper = vupper
                    upper_inclusive = False
                if lower is None or version > lower:
                    lower = version
                    lower_inclusive = True
            case "!=":
                exclusions.add(version)
            case _:
                raise AssertionError(f"Unknown specifier: {specifier}")

    if upper:
        if upper_inclusive and upper in exclusions:
            upper_inclusive = False

        if upper_inclusive:
            exclusions = {e for e in exclusions if e <= upper}
        else:
            exclusions = {e for e in exclusions if e < upper}

    if lower:
        if lower_inclusive and lower in exclusions:
            lower_inclusive = False

        if lower_inclusive:
            exclusions = {e for e in exclusions if e >= lower}
        else:
            exclusions = {e for e in exclusions if e > lower}

    if upper is not None and lower is not None:
        if upper_inclusive and lower_inclusive:
            assert lower <= upper, f"Empty specifier set: {specifier_set}"
        else:
            assert lower < upper, f"Empty specifier set: {specifier_set}"

    return Bounds(specifier_set, upper, upper_inclusive, lower, lower_inclusive, exclusions)
