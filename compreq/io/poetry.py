from typing import Any, Collection, Mapping, Sequence

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from tomlkit import inline_table

from compreq.classifiers import set_python_classifiers
from compreq.io.pyproject import PyprojectFile
from compreq.lazy import AnyReleaseSet, AnyRequirement
from compreq.operators import REL_MAJOR, CeilLazyVersion
from compreq.root import CompReq


class PoetryPyprojectFile(PyprojectFile):
    def get_requirements(self, group: str | None = None) -> Mapping[str, Requirement]:
        return {
            package: self._parse_requirement(package, toml)
            for package, toml in self._get_dependencies(group).items()
        }

    def _parse_requirement(self, package: str, toml: Any) -> Requirement:
        result = Requirement.__new__(Requirement)
        result.name = package
        result.url = None
        result.extras = set()
        result.specifier = SpecifierSet()
        result.marker = None

        if isinstance(toml, dict):
            if "url" in toml:
                result.url = toml["url"]
            if "path" in toml:
                result.url = f"file://{toml['path']}"
            if "git" in toml:
                result.url = f"git+{toml['git']}"
            if "extras" in toml:
                result.extras = set(toml["extras"])
            if "version" in toml:
                result.specifier = self._parse_specifier_set(toml["version"])
            if "markers" in toml:
                result.marker = Marker(toml["markers"])
        else:
            result.specifier = self._parse_specifier_set(toml)

        return result

    def _parse_specifier_set(self, specifier_set: str) -> SpecifierSet:
        result = SpecifierSet()
        for specifier in specifier_set.split(","):
            if specifier.startswith("^"):
                version = Version(specifier[1:])
                upper = CeilLazyVersion.ceil(REL_MAJOR, version)
                result &= SpecifierSet(f"<{upper},>={version}")
            elif specifier.startswith("~"):
                result &= SpecifierSet(f"~={specifier[1:]}")
            else:
                result &= SpecifierSet(specifier)
        return result

    def set_requirements(
        self,
        cr: CompReq,
        requirements: Mapping[str, AnyRequirement] | Collection[AnyRequirement],
        group: str | None = None,
    ) -> None:
        requirements_collection = (
            requirements.values() if hasattr(requirements, "values") else requirements
        )
        assert isinstance(requirements_collection, Collection)
        requirements_toml = self._get_dependencies(group)
        requirements_toml.clear()
        for requirement in requirements_collection:
            r = cr.resolve_requirement(requirement)
            requirements_toml[r.name] = self._format_requirement(r)

    def _format_requirement(self, requirement: Requirement) -> Any:
        result = inline_table()

        if requirement.url is not None:
            url = requirement.url
            if url.startswith("file://"):
                result["path"] = url[7:]
            elif url.startswith("git+"):
                result["git"] = url[4:]
            else:
                result["url"] = url
        if requirement.extras:
            result["extras"] = sorted(requirement.extras)
        if requirement.specifier:
            result["version"] = self._format_specifier_set(requirement.specifier)
        if requirement.marker is not None:
            result["markers"] = str(requirement.marker)

        return result if list(result) != ["version"] else result["version"]

    def _format_specifier_set(self, specifier_set: SpecifierSet) -> str:
        specifiers = []
        for specifier in specifier_set:
            if specifier.operator == "~=":
                specifiers.append(f"~{specifier.version}")
            else:
                specifiers.append(str(specifier))
        return ",".join(sorted(specifiers))

    def _get_poetry(self) -> Any:
        return self.toml["tool"]["poetry"]

    def _get_dependencies(self, group: str | None) -> Any:
        if group is None:
            return self._get_poetry()["dependencies"]
        else:
            return self._get_poetry()["group"][group]["dependencies"]

    def get_classifiers(self) -> Sequence[str]:
        return list(self._get_poetry()["classifiers"])

    def set_classifiers(self, classifiers: Sequence[str]) -> None:
        toml = self._get_poetry()["classifiers"]
        toml.clear()
        toml.extend(classifiers)
        toml.multiline(True)

    def set_python_classifiers(self, cr: CompReq, python_releases: AnyReleaseSet) -> None:
        self.set_classifiers(set_python_classifiers(cr, python_releases, self.get_classifiers()))
