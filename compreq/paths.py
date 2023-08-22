from os import PathLike
from typing import TypeAlias

AnyPath: TypeAlias = PathLike[str] | str
