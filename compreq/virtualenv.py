import json
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from typing import Iterator

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from compreq.factory import make_requirement
from compreq.levels import MINOR
from compreq.paths import AnyPath
from compreq.requirements import RequirementSet
from compreq.rounding import floor
from compreq.scripts import get_dist_metadata


def _run(command: str) -> str:
    result = subprocess.run(
        command,
        shell=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout = result.stdout.decode("utf-8")
    assert result.returncode == 0, (command, stdout)
    return stdout


@dataclass
class DistMetadata:
    package: str
    version: Version
    requires: RequirementSet


class VirtualEnv:
    def __init__(self, path: AnyPath) -> None:
        self._path = Path(path)

    def run(self, command: str) -> str:
        return _run(f". {self._path}/bin/activate && {command}")

    def install(self, requirement_set: RequirementSet, deps: bool = True) -> None:
        tokens = ["pip install"]
        if not deps:
            tokens.append("--no-deps")
        tokens.extend(f'"{r}"' for r in requirement_set.values())
        self.run(" ".join(tokens))

    def package_metadata(self, package: str) -> DistMetadata:
        output = self.run(f"python {get_dist_metadata.__file__} {package}")
        data = json.loads(output)
        version = Version(data["version"])
        python_requires = make_requirement(
            package="python", specifier=SpecifierSet(data["requires_python"])
        )
        requires = [python_requires] + [Requirement(r) for r in data["requires"]]
        return DistMetadata(
            package=package,
            version=version,
            requires=RequirementSet.new(requires),
        )


def create_venv(path: AnyPath, python_version: str | Version) -> VirtualEnv:
    if isinstance(python_version, str):
        python_version = Version(python_version)
    assert isinstance(python_version, Version)
    python_version = floor(MINOR, python_version, keep_trailing_zeros=False)
    path_ = Path(path)
    _run(f"virtualenv -p python{python_version} {path_}")
    return VirtualEnv(path_)


def remove_venv(venv: VirtualEnv) -> None:
    # pylint: disable=protected-access
    rmtree(venv._path)
    venv._path = None  # type: ignore[assignment]


@contextmanager
def temp_venv(python_version: str | Version, clean_on_error: bool = True) -> Iterator[VirtualEnv]:
    path = mkdtemp("compreq_venv")
    venv = create_venv(path, python_version)
    if clean_on_error:
        try:
            yield venv
        finally:
            remove_venv(venv)
    else:
        yield venv
        remove_venv(venv)
