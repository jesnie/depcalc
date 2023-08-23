from os import PathLike
from typing import TypeAlias

AnyPath: TypeAlias = PathLike[str] | str
"""Type alias for anything that can be converted to a `pathlib.Path`."""
