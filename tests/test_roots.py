from unittest.mock import MagicMock

from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from compreq import (
    CompReq,
    Context,
    LazyRelease,
    LazyReleaseSet,
    LazyRequirement,
    LazySpecifier,
    LazySpecifierSet,
    LazyVersion,
    PackageContext,
)
from tests.utils import fake_release, fake_release_set


def test_comp_req__resolve_release() -> None:
    context = MagicMock(Context)
    pcontext = MagicMock(PackageContext)
    context.for_package.return_value = pcontext

    release = fake_release(package="foo.bar", version="1.2.3")
    lazy = MagicMock(LazyRelease)
    lazy.resolve.return_value = release

    cr = CompReq(context)

    assert release == cr.resolve_release("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(pcontext)
    context.for_package.assert_called_once_with("foo.bar")


def test_comp_req__resolve_release_set() -> None:
    context = MagicMock(Context)
    pcontext = MagicMock(PackageContext)
    context.for_package.return_value = pcontext

    release_set = fake_release_set(package="foo.bar", releases=["1.2.3", "1.2.4", "1.2.5"])
    lazy = MagicMock(LazyReleaseSet)
    lazy.resolve.return_value = release_set

    cr = CompReq(context)

    assert release_set == cr.resolve_release_set("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(pcontext)
    context.for_package.assert_called_once_with("foo.bar")


def test_comp_req__resolve_version() -> None:
    context = MagicMock(Context)
    pcontext = MagicMock(PackageContext)
    context.for_package.return_value = pcontext

    version = Version("1.2.3")
    lazy = MagicMock(LazyVersion)
    lazy.resolve.return_value = version

    cr = CompReq(context)

    assert version == cr.resolve_version("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(pcontext)
    context.for_package.assert_called_once_with("foo.bar")


def test_comp_req__resolve_specifier() -> None:
    context = MagicMock(Context)
    pcontext = MagicMock(PackageContext)
    context.for_package.return_value = pcontext

    specifier = Specifier("~=1.2.3")
    lazy = MagicMock(LazySpecifier)
    lazy.resolve.return_value = specifier

    cr = CompReq(context)

    assert specifier == cr.resolve_specifier("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(pcontext)
    context.for_package.assert_called_once_with("foo.bar")


def test_comp_req__resolve_specifier_set() -> None:
    context = MagicMock(Context)
    pcontext = MagicMock(PackageContext)
    context.for_package.return_value = pcontext

    specifier_set = SpecifierSet("<2.0.0,>=1.2.3")
    lazy = MagicMock(LazySpecifierSet)
    lazy.resolve.return_value = specifier_set

    cr = CompReq(context)

    assert specifier_set == cr.resolve_specifier_set("foo.bar", lazy)
    lazy.resolve.assert_called_once_with(pcontext)
    context.for_package.assert_called_once_with("foo.bar")


def test_comp_req__resolve_requirement() -> None:
    context = MagicMock(Context)

    requirement = Requirement("foo.bar~=1.2.3")
    lazy = MagicMock(LazyRequirement)
    lazy.resolve.return_value = requirement

    cr = CompReq(context)

    assert requirement == cr.resolve_requirement(lazy)
    lazy.resolve.assert_called_once_with(context)
