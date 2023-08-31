import pytest
from packaging.version import Version

import compreq as cr


@pytest.mark.parametrize(
    "specifier,expected",
    [
        (
            cr.version.require("<=", "1.0.0"),
            cr.EagerLazySpecifier(cr.SpecifierOperator.LE, cr.EagerLazyVersion(Version("1.0.0"))),
        ),
        (
            cr.version(">=", "1.0.0"),
            cr.EagerLazySpecifier(cr.SpecifierOperator.GE, cr.EagerLazyVersion(Version("1.0.0"))),
        ),
        (cr.version.compatible("1.1.0"), cr.version("~=", "1.1.0")),
        (cr.version.exclude("1.2.0"), cr.version("!=", "1.2.0")),
        (cr.version.ne("1.3.0"), cr.version("!=", "1.3.0")),
        (cr.version != "1.4.0", cr.version("!=", "1.4.0")),
        (cr.version.match("1.5.0"), cr.version("==", "1.5.0")),
        (cr.version.eq("1.6.0"), cr.version("==", "1.6.0")),
        (cr.version == "1.7.0", cr.version("==", "1.7.0")),
        (cr.version.less("1.8.0"), cr.version("<", "1.8.0")),
        (cr.version.lt("1.9.0"), cr.version("<", "1.9.0")),
        (cr.version < "1.10.0", cr.version("<", "1.10.0")),
        (cr.version.greater("1.11.0"), cr.version(">", "1.11.0")),
        (cr.version.gt("1.12.0"), cr.version(">", "1.12.0")),
        (cr.version > "1.13.0", cr.version(">", "1.13.0")),
        (cr.version.less_or_equal("1.14.0"), cr.version("<=", "1.14.0")),
        (cr.version.le("1.15.0"), cr.version("<=", "1.15.0")),
        (cr.version <= "1.16.0", cr.version("<=", "1.16.0")),
        (cr.version.greater_or_equal("1.17.0"), cr.version(">=", "1.17.0")),
        (cr.version.ge("1.18.0"), cr.version(">=", "1.18.0")),
        (cr.version >= "1.19.0", cr.version(">=", "1.19.0")),
        (cr.version.arbitrary_equal("1.20.0"), cr.version("===", "1.20.0")),
    ],
)
def test_version_token(specifier: cr.LazySpecifier, expected: cr.LazySpecifier) -> None:
    assert specifier == expected
