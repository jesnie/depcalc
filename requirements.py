import re

from packaging.specifiers import SpecifierSet

import compreq.operators as o
from compreq.context import DefaultContext
from compreq.io.poetry import PoetryPyprojectFile
from compreq.lazy import AnySpecifierSet
from compreq.root import CompReq


def get_python_specifier(pyproject: PoetryPyprojectFile) -> SpecifierSet:
    prev_python = pyproject.get_requirements()["python"].specifier
    match = re.fullmatch("<4.0.0,(>=.*)", str(prev_python))
    assert match
    return SpecifierSet(match[1])


def set_python_version(cr: CompReq, pyproject: PoetryPyprojectFile) -> AnySpecifierSet:
    floor = cr.resolve_version("python", o.floor_ver(o.MINOR, o.max_ver(o.min_age(years=3))))
    ceil = cr.resolve_version("python", o.ceil_ver(o.MAJOR, o.max_ver()))
    specfiers = o.version(">=", floor) & o.version("<", ceil)

    pyproject.set_python_classifiers(cr, specfiers)

    tool = pyproject.toml["tool"]
    tool["isort"]["py_version"] = int(f"{floor.major}{floor.minor}")
    tool["black"]["target-version"] = [f"py{floor.major}{floor.minor}"]
    tool["mypy"]["python_version"] = f"{floor.major}.{floor.minor}"

    return specfiers


def main() -> None:
    with PoetryPyprojectFile.open() as pyproject:
        ctx = DefaultContext(get_python_specifier(pyproject))
        cr = CompReq(ctx)

        python_specifiers = set_python_version(cr, pyproject)

        default_range = o.version(
            ">=",
            o.floor_ver(
                o.REL_MINOR,
                o.minimum_ver(
                    o.max_ver(o.min_age(years=1)),
                    o.min_ver(o.count(o.MINOR, 3)),
                ),
            ),
        ) & o.version("<", o.ceil_ver(o.REL_MAJOR, o.max_ver()))
        dev_range = o.version(">=", o.floor_ver(o.REL_MINOR, o.max_ver())) & o.version(
            "<", o.ceil_ver(o.REL_MINOR, o.max_ver())
        )

        pyproject.set_requirements(
            cr,
            [
                o.pkg("beautifulsoup4") & default_range,
                o.pkg("packaging") & default_range,
                o.pkg("pip") & default_range,
                o.pkg("python") & python_specifiers,
                o.pkg("python-dateutil") & default_range,
                o.pkg("requests") & default_range,
                o.pkg("typing-extensions") & default_range,
            ],
        )
        pyproject.set_requirements(
            cr,
            [
                o.pkg("black") & dev_range,
                o.pkg("isort") & dev_range,
                o.pkg("mypy") & dev_range,
                o.pkg("pylint") & dev_range,
                o.pkg("pytest") & dev_range,
                o.pkg("taskipy") & dev_range,
                o.pkg("tomlkit") & dev_range,
                o.pkg("types-beautifulsoup4") & default_range,
                o.pkg("types-python-dateutil") & default_range,
                o.pkg("types-requests") & default_range,
            ],
            "dev",
        )

        print(pyproject)


if __name__ == "__main__":
    main()
