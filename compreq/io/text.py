from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Collection, Iterator, Mapping

from packaging.requirements import Requirement
from typing_extensions import Self

from compreq.lazy import AnyRequirement
from compreq.paths import AnyPath
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
        self.requirements = {}
        if self.path.exists():
            with open(self.path, "rt", encoding="utf-8") as fp:
                for line in fp.readlines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("#"):
                        continue
                    r = Requirement(line)
                    self.requirements[r.name] = r

    def close(self) -> None:
        self.path.write_text(str(self), encoding="utf-8")

    @classmethod
    @contextmanager
    def open(cls, path: AnyPath) -> Iterator[Self]:
        f = cls(path)
        yield f
        f.close()

    def get_requirements(self) -> Mapping[str, Requirement]:
        return dict(self.requirements)

    def set_requirements(
        self,
        cr: CompReq,
        requirements: Mapping[str, AnyRequirement] | Collection[AnyRequirement],
    ) -> None:
        requirements_collection = (
            requirements.values() if hasattr(requirements, "values") else requirements
        )
        resolved_requirements = [cr.resolve_requirement(r) for r in requirements_collection]
        self.requirements = {r.name: r for r in resolved_requirements}

    def __str__(self) -> str:
        return "\n".join(str(r) for _, r in sorted(self.requirements.items())) + "\n"
