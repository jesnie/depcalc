from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass

from packaging.requirements import Requirement


@dataclass(frozen=True)
class RequirementSet(Mapping[str, Requirement]):
    """
    A set of requirements.

    Despite the name this functions more like a mapping from distribution name to the requirements
    for that distribution.
    """

    requirements: Mapping[str, Requirement]

    @staticmethod
    def new(requirements: Mapping[str, Requirement] | Iterable[Requirement]) -> RequirementSet:
        """Helper function for creating a `RequirementSet` from any collection."""
        if not isinstance(requirements, Mapping):
            return RequirementSet({r.name: r for r in requirements})
        else:
            return RequirementSet(dict(requirements))

    def __getitem__(self, key: str) -> Requirement:
        return self.requirements[key]

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self.requirements))

    def __len__(self) -> int:
        return len(self.requirements)
