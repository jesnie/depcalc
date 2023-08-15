import pytest
from packaging.version import Version

import compreq.factory as f
from compreq.lazy import EagerLazyVersion, LazySpecifier, SpecifierOperator


@pytest.mark.parametrize(
    "specifier,expected",
    [
        (
            f.version.require("<=", "1.0.0"),
            LazySpecifier(SpecifierOperator.LE, EagerLazyVersion(Version("1.0.0"))),
        ),
        (
            f.version(">=", "1.0.0"),
            LazySpecifier(SpecifierOperator.GE, EagerLazyVersion(Version("1.0.0"))),
        ),
        (f.version.compatible("1.1.0"), f.version("~=", "1.1.0")),
        (f.version.exclude("1.2.0"), f.version("!=", "1.2.0")),
        (f.version.ne("1.3.0"), f.version("!=", "1.3.0")),
        (f.version != "1.4.0", f.version("!=", "1.4.0")),
        (f.version.match("1.5.0"), f.version("==", "1.5.0")),
        (f.version.eq("1.6.0"), f.version("==", "1.6.0")),
        (f.version == "1.7.0", f.version("==", "1.7.0")),
        (f.version.less("1.8.0"), f.version("<", "1.8.0")),
        (f.version.lt("1.9.0"), f.version("<", "1.9.0")),
        (f.version < "1.10.0", f.version("<", "1.10.0")),
        (f.version.greater("1.11.0"), f.version(">", "1.11.0")),
        (f.version.gt("1.12.0"), f.version(">", "1.12.0")),
        (f.version > "1.13.0", f.version(">", "1.13.0")),
        (f.version.less_or_equal("1.14.0"), f.version("<=", "1.14.0")),
        (f.version.le("1.15.0"), f.version("<=", "1.15.0")),
        (f.version <= "1.16.0", f.version("<=", "1.16.0")),
        (f.version.greater_or_equal("1.17.0"), f.version(">=", "1.17.0")),
        (f.version.ge("1.18.0"), f.version(">=", "1.18.0")),
        (f.version >= "1.19.0", f.version(">=", "1.19.0")),
        (f.version.arbitrary_equal("1.20.0"), f.version("===", "1.20.0")),
    ],
)
def test_version_token(specifier: LazySpecifier, expected: LazySpecifier) -> None:
    assert specifier == expected
