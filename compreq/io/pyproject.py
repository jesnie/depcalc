from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from tomlkit import dump, dumps, load
from typing_extensions import Self

from compreq.paths import AnyPath


class PyprojectFile:
    """
    Wrapper around a generic `pyproject.toml`.

    Usage::

        with PyprojectFile.open() as pyproject:
            pyproject.toml[...] = ...
    """

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
