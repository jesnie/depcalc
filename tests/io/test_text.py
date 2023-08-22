from pathlib import Path
from unittest.mock import MagicMock

from packaging.requirements import Requirement

from compreq.contexts import Context
from compreq.io.text import TextRequirementsFile
from compreq.lazy import get_lazy_requirement
from compreq.roots import CompReq

TEXT_REQUIREMENTS = """pack1!=1.2.5,<2.0.0,>=1.2.3
pack2<=1.9.0,>1.2.3
pack3==1.2.5
pack4~=1.2
pack5<2.0.0,>=1.2.3
pack6<0.2.0,>=0.1.0
packextra[extra1,extra2]<2.0.0,>=1.2.3
packgit@ git+https://github.com/pack6/pack6
packmarker>=1.2.3; platform_system != "Darwin" or platform_machine != "arm64"
packpath@ file:///home/compreq
packurl@ http://www.test.com/test/pack7-1.2.3.tar.gz
"""

REQUIREMENTS = {
    "pack1": Requirement("pack1!=1.2.5,<2.0.0,>=1.2.3"),
    "pack2": Requirement("pack2<=1.9.0,>1.2.3"),
    "pack3": Requirement("pack3==1.2.5"),
    "pack4": Requirement("pack4~=1.2"),
    "pack5": Requirement("pack5<2.0.0,>=1.2.3"),
    "pack6": Requirement("pack6<0.2.0,>=0.1.0"),
    "packextra": Requirement("packextra[extra1, extra2]<2.0.0,>=1.2.3"),
    "packgit": Requirement("packgit@git+https://github.com/pack6/pack6"),
    "packmarker": Requirement(
        "packmarker>=1.2.3; platform_system != 'Darwin' or platform_machine != 'arm64'"
    ),
    "packpath": Requirement("packpath@file:///home/compreq"),
    "packurl": Requirement("packurl@http://www.test.com/test/pack7-1.2.3.tar.gz"),
}


def test_text_requirements_file__get_requirements(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text(TEXT_REQUIREMENTS)

    with TextRequirementsFile.open(requirements_path) as requirements:
        assert REQUIREMENTS == requirements.get_requirements()


def test_text_requirements_file__set_requirements(tmp_path: Path) -> None:
    requirements_path = tmp_path / "requirements.txt"
    requirements_path.write_text(
        """

  # A comment

foo<2.0.0,>=1.2.3
"""
    )

    with TextRequirementsFile.open(requirements_path) as requirements:
        compreq = MagicMock(CompReq)
        compreq.context = MagicMock(Context)
        compreq.resolve_requirement.side_effect = lambda r: get_lazy_requirement(r).resolve(
            compreq.context
        )

        requirements.set_requirements(compreq, REQUIREMENTS)

    assert TEXT_REQUIREMENTS == requirements_path.read_text()
