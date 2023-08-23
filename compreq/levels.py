from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final, TypeAlias

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


MAJOR: Final[Level] = IntLevel(0)
MINOR: Final[Level] = IntLevel(1)
MICRO: Final[Level] = IntLevel(2)
REL_MAJOR: Final[Level] = RelativeToFirstNonZeroLevel(0)
REL_MINOR: Final[Level] = RelativeToFirstNonZeroLevel(1)
REL_MICRO: Final[Level] = RelativeToFirstNonZeroLevel(3)


AnyLevel: TypeAlias = int | Level


def get_level(level: AnyLevel) -> Level:
    if isinstance(level, int):
        level = IntLevel(level)
    if isinstance(level, Level):
        return level
    raise AssertionError(f"Unknown type of level: {type(level)}")
