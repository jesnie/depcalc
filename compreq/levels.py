from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeAlias

from packaging.version import Version


class Level(ABC):
    @abstractmethod
    def index(self, version: Version) -> int:
        ...


@dataclass(order=True, frozen=True)
class IntLevel(Level):
    level: int

    def index(self, version: Version) -> int:
        return self.level


@dataclass(order=True, frozen=True)
class RelativeToFirstNonZeroLevel(Level):
    relative_level: int

    def __post_init__(self) -> None:
        assert self.relative_level >= 0

    def index(self, version: Version) -> int:
        for i, r in enumerate(version.release):
            if r != 0:
                return i + self.relative_level
        raise AssertionError(f"No non-zero segment found in {version}")


AnyLevel: TypeAlias = int | Level


def get_level(level: AnyLevel) -> Level:
    if isinstance(level, int):
        level = IntLevel(level)
    if isinstance(level, Level):
        return level
    raise AssertionError(f"Unknown type of level: {type(level)}")
