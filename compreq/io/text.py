from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from packaging.requirements import Requirement
from typing_extensions import Self

from compreq.lazy import AnyRequirementSet
from compreq.paths import AnyPath
from compreq.requirements import RequirementSet
from compreq.roots import CompReq


class TextRequirementsFile:
    """
    Wrapper around a `requirements.txt` file.

    Usage::

        with TextRequirementsFile.open("requirements.txt") as requirements_file:
            requirements_file.set_requirements(...)
    """

    def __init__(self, path: AnyPath) -> None:
        self.path = Path(path)
        requirements = []
        if self.path.exists():
            with open(self.path, "rt", encoding="utf-8") as fp:
                for line in fp.readlines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("#"):
                        continue
                    requirements.append(Requirement(line))
        self.requirements = RequirementSet.new(requirements)

    def close(self) -> None:
        self.path.write_text(str(self), encoding="utf-8")

    @classmethod
    @contextmanager
    def open(cls, path: AnyPath) -> Iterator[Self]:
        f = cls(path)
        yield f
        f.close()

    def get_requirements(self) -> RequirementSet:
        return self.requirements

    def set_requirements(
        self,
        cr: CompReq,
        requirement_set: AnyRequirementSet,
    ) -> None:
        self.requirements = cr.resolve_requirement_set(requirement_set)

    def __str__(self) -> str:
        return "\n".join(str(r) for r in self.requirements.values()) + "\n"
