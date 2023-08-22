from __future__ import annotations

import re
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

from typing_extensions import Self

from compreq.paths import AnyPath


class TextReFile:
    def __init__(self, path: AnyPath) -> None:
        self.path = Path(path)
        self.contents = ""
        if self.path.exists():
            self.contents = self.path.read_text(encoding="utf-8")

    def close(self) -> None:
        self.path.write_text(self.contents, encoding="utf-8")

    @classmethod
    @contextmanager
    def open(cls, path: AnyPath) -> Iterator[Self]:
        f = cls(path)
        yield f
        f.close()

    def sub(
        self,
        pattern: str | re.Pattern[str],
        repl: str | Callable[[re.Match[str]], str],
        count: int = 0,
        flags: int = re.MULTILINE,
    ) -> int:
        self.contents, result = re.subn(pattern, repl, self.contents, count, flags)
        return result

    def __str__(self) -> str:
        return self.contents
