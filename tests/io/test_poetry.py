# pylint: disable=line-too-long

# Examples:
# argon2-cffi = {extras = ["argon2"], version = "^23.1.0"}
# pip = {git = "https://github.com/pypa/pip"}
# beautifulsoup = {url = "http://www.crummy.com/software/BeautifulSoup/unreleased/4.x/BeautifulSoup-4.0b.tar.gz"}
# tensorflow = {version = ">=2.8.0", markers = "platform_system != \"Darwin\" or platform_machine != \"arm64\""}
# check-shapes = {path = "/home/foo/src/check_shapes"}

from pathlib import Path
from unittest.mock import MagicMock

from packaging.requirements import Requirement

from compreq import (
    CompReq,
    Context,
    PoetryPyprojectFile,
    RequirementSet,
    get_lazy_release_set,
    get_lazy_requirement_set,
)
from tests.utils import fake_release_set

PYPROJECT_CONTENTS = """
[tool.poetry]
name = "compreq"
version = "0.1.0"

[tool.poetry.dependencies]
pack1 = "!=1.2.5,<2.0.0,>=1.2.3"
pack2 = "<=1.9.0,>1.2.3"
pack3 = "==1.2.5"
pack4 = "~1.2"
pack5 = "^1.2.3"
pack6 = "^0.1.0"
packextra = {extras = ["extra1", "extra2"], version = "^1.2.3"}
packgit = {git = "https://github.com/pack6/pack6"}
packmarker = {version = ">=1.2.3", markers = "platform_system != \\"Darwin\\" or platform_machine != 'arm64'"}
packpath = {path = "/home/compreq"}
packurl = {url = "http://www.test.com/test/pack7-1.2.3.tar.gz"}

[tool.poetry.group.dev.dependencies]
pack-dev1 = "<2.0.0,>=1.2.3"
"""

PYPROJECT_CONTENTS_AFTER = """
[tool.poetry]
name = "compreq"
version = "0.1.0"

[tool.poetry.dependencies]
pack1 = "!=1.2.5,<2.0.0,>=1.2.3"
pack2 = "<=1.9.0,>1.2.3"
pack3 = "==1.2.5"
pack4 = "~1.2"
pack5 = "<2.0.0,>=1.2.3"
pack6 = "<0.2.0,>=0.1.0"
packextra = {extras = ["extra1", "extra2"], version = "<2.0.0,>=1.2.3"}
packgit = {git = "https://github.com/pack6/pack6"}
packmarker = {version = ">=1.2.3", markers = "platform_system != \\"Darwin\\" or platform_machine != \\"arm64\\""}
packpath = {path = "/home/compreq"}
packurl = {url = "http://www.test.com/test/pack7-1.2.3.tar.gz"}

[tool.poetry.group.dev.dependencies]
pack-dev1 = "<2.0.0,>=1.2.3"
"""

MAIN_REQUIREMENTS = RequirementSet.new(
    [
        Requirement("pack1!=1.2.5,<2.0.0,>=1.2.3"),
        Requirement("pack2<=1.9.0,>1.2.3"),
        Requirement("pack3==1.2.5"),
        Requirement("pack4~=1.2"),
        Requirement("pack5<2.0.0,>=1.2.3"),
        Requirement("pack6<0.2.0,>=0.1.0"),
        Requirement("packextra[extra1, extra2]<2.0.0,>=1.2.3"),
        Requirement("packurl@http://www.test.com/test/pack7-1.2.3.tar.gz"),
        Requirement("packpath@file:///home/compreq"),
        Requirement("packgit@git+https://github.com/pack6/pack6"),
        Requirement(
            "packmarker>=1.2.3; platform_system != 'Darwin' or platform_machine != 'arm64'"
        ),
    ]
)

DEV_REQUIREMENTS = RequirementSet.new(
    [
        Requirement("pack-dev1<2.0.0,>=1.2.3"),
    ]
)


def test_poetry_pyproject_file__get_requirements(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(PYPROJECT_CONTENTS)

    with PoetryPyprojectFile.open(pyproject_path) as pyproject:
        assert MAIN_REQUIREMENTS == pyproject.get_requirements()
        assert DEV_REQUIREMENTS == pyproject.get_requirements("dev")


def test_poetry_pyproject_file__set_requirements(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[tool.poetry]
name = "compreq"
version = "0.1.0"

[tool.poetry.dependencies]

[tool.poetry.group.dev.dependencies]
"""
    )

    with PoetryPyprojectFile.open(pyproject_path) as pyproject:
        compreq = MagicMock(CompReq)
        compreq.context = MagicMock(Context)
        compreq.resolve_requirement_set.side_effect = lambda r: get_lazy_requirement_set(r).resolve(
            compreq.context
        )

        pyproject.set_requirements(
            compreq,
            MAIN_REQUIREMENTS,
        )
        pyproject.set_requirements(compreq, DEV_REQUIREMENTS, "dev")

    assert PYPROJECT_CONTENTS_AFTER == pyproject_path.read_text()


def test_poetry_pyproject_file__get_classifiers(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[tool.poetry]
name = "compreq"
version = "0.1.0"
classifiers = [
    "test1",
    "test2",
    "test3",
]
"""
    )

    with PoetryPyprojectFile.open(pyproject_path) as pyproject:
        assert ["test1", "test2", "test3"] == pyproject.get_classifiers()


def test_poetry_pyproject_file__set_classifiers(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[tool.poetry]
name = "compreq"
version = "0.1.0"
classifiers = [
    "chaff1",
    "chaff2",
]
"""
    )

    with PoetryPyprojectFile.open(pyproject_path) as pyproject:
        pyproject.set_classifiers(["test1", "test2", "test3"])

    assert (
        """
[tool.poetry]
name = "compreq"
version = "0.1.0"
classifiers = [
    "test1",
    "test2",
    "test3",
]
"""
        == pyproject_path.read_text()
    )


def test_poetry_pyproject_file__set_python_classifiers(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[tool.poetry]
name = "compreq"
version = "0.1.0"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Typing :: Typed",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
"""
    )

    cr = MagicMock(CompReq)
    python_releases = fake_release_set(
        package="python",
        releases=[
            # NOT sorted:
            "2.6.1",
            "3.1.1",
            "3.0.0",
            "2.7.2",
            "3.0.1",
            "2.7.0",
            "2.7.1",
            "3.1.2",
        ],
    )
    lazy_python_releases = get_lazy_release_set(python_releases)
    cr.resolve_release_set.return_value = python_releases

    with PoetryPyprojectFile.open(pyproject_path) as pyproject:
        pyproject.set_python_classifiers(cr, lazy_python_releases)

    assert (
        """
[tool.poetry]
name = "compreq"
version = "0.1.0"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Typing :: Typed",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.0",
    "Programming Language :: Python :: 3.1",
]
"""
        == pyproject_path.read_text()
    )
    cr.resolve_release_set.assert_called_once_with("python", lazy_python_releases)
