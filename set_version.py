import argparse
import re

import toml

VERSION_RE = re.compile(r"v\d+\.\d+\.\d+(-.*)?")
PYPROJECT_FILE = "pyproject.toml"


def parse_version(github_ref: str) -> str:
    assert VERSION_RE.fullmatch(github_ref)
    return github_ref[1:]


def set_version(version: str) -> None:
    with open(PYPROJECT_FILE, "rt", encoding="utf-8") as fi:
        config = toml.load(fi)

    config["tool"]["poetry"]["version"] = version

    with open(PYPROJECT_FILE, "wt", encoding="utf-8") as fo:
        toml.dump(config, fo)


def main() -> None:
    parser = argparse.ArgumentParser(description="Set the project version in pyproject.toml.")
    parser.add_argument("ref_name", help="The github.ref_name parameter from the Github action")
    args = parser.parse_args()
    version = parse_version(args.ref_name)
    set_version(version)


if __name__ == "__main__":
    main()
