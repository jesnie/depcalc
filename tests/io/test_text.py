import asyncio
from pathlib import Path
from unittest.mock import MagicMock

from packaging.requirements import Requirement

from compreq import (
    CompReq,
    Context,
    RequirementSet,
    TextRequirementsFile,
    get_lazy_requirement_set,
)

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

REQUIREMENTS = RequirementSet.new(
    [
        Requirement("pack1!=1.2.5,<2.0.0,>=1.2.3"),
        Requirement("pack2<=1.9.0,>1.2.3"),
        Requirement("pack3==1.2.5"),
        Requirement("pack4~=1.2"),
        Requirement("pack5<2.0.0,>=1.2.3"),
        Requirement("pack6<0.2.0,>=0.1.0"),
        Requirement("packextra[extra1, extra2]<2.0.0,>=1.2.3"),
        Requirement("packgit@git+https://github.com/pack6/pack6"),
        Requirement(
            "packmarker>=1.2.3; platform_system != 'Darwin' or platform_machine != 'arm64'"
        ),
        Requirement("packpath@file:///home/compreq"),
        Requirement("packurl@http://www.test.com/test/pack7-1.2.3.tar.gz"),
    ]
)


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
        compreq.resolve_requirement_set.side_effect = lambda r: asyncio.run(
            get_lazy_requirement_set(r).resolve(compreq.context)
        )

        requirements.set_requirements(compreq, REQUIREMENTS)

    assert TEXT_REQUIREMENTS == requirements_path.read_text()
