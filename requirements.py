import re
from pathlib import Path
from typing import Any

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, parse
from ruamel.yaml import YAML

import compreq.operators as o
from compreq.context import DefaultContext
from compreq.io.poetry import PoetryPyprojectFile
from compreq.lazy import AnySpecifierSet
from compreq.release import ReleaseSet
from compreq.root import CompReq


def get_python_specifier(pyproject: PoetryPyprojectFile) -> SpecifierSet:
    prev_python = pyproject.get_requirements()["python"].specifier
    match = re.fullmatch("<4.0.0,(>=.*)", str(prev_python))
    assert match
    return SpecifierSet(match[1])


def set_python_version_in_github_actions(python_release_set: ReleaseSet) -> None:
    minor_versions = sorted(
        set(
            o.FloorLazyVersion.floor(o.MINOR, r.version, keep_trailing_zeros=False)
            for r in python_release_set.releases
        )
    )
    default_version = min(minor_versions)

    def update_python_version(yaml: Any) -> None:
        if isinstance(yaml, dict):
            if "python-version" in yaml:
                try:
                    parse(yaml["python-version"])
                    yaml["python-version"] = str(default_version)
                except InvalidVersion:
                    pass
            if "matrix" in yaml and "python" in yaml["matrix"]:
                yaml["matrix"]["python"] = [str(v) for v in minor_versions]
            for value in yaml.values():
                update_python_version(value)
        elif isinstance(yaml, list):
            for value in yaml:
                update_python_version(value)

    yaml = YAML()
    for yaml_path in Path(".github/workflows").glob("*.yml"):
        action = yaml.load(yaml_path)
        update_python_version(action)
        yaml.dump(action, yaml_path)


def set_python_version(cr: CompReq, pyproject: PoetryPyprojectFile) -> AnySpecifierSet:
    floor = cr.resolve_version("python", o.floor_ver(o.MINOR, o.max_ver(o.min_age(years=3))))
    ceil = cr.resolve_version("python", o.ceil_ver(o.MAJOR, o.max_ver()))
    specfiers = o.version(">=", floor) & o.version("<", ceil)

    pyproject.set_python_classifiers(cr, specfiers)
    set_python_version_in_github_actions(cr.resolve_release_set("python", specfiers))

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
                o.pkg("ruamel.yaml") & default_range,
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
