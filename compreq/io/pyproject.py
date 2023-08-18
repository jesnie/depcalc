from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from tomlkit import dump, dumps, load
from typing_extensions import Self

from compreq.path import AnyPath


class PyprojectFile:
    def __init__(self, path: AnyPath) -> None:
        self.path = Path(path)
        with open(self.path, "rt", encoding="utf-8") as fp:
            self.toml: Any = load(fp)

    def close(self) -> None:
        with open(self.path, "wt", encoding="utf-8") as fp:
            dump(self.toml, fp)

    @classmethod
    @contextmanager
    def open(cls, path: AnyPath = "pyproject.toml") -> Iterator[Self]:
        f = cls(path)
        yield f
        f.close()

    def __str__(self) -> str:
        return dumps(self.toml)
