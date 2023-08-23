import datetime as dt

from packaging.specifiers import SpecifierSet
from pytest import MonkeyPatch

from compreq import DefaultContext, ReleaseSet
from tests.utils import fake_release_set, utc


def test_default_context(monkeypatch: MonkeyPatch) -> None:
    fake_now = utc(dt.datetime(2023, 8, 22, 14, 20))

    python_specifiers_ = SpecifierSet("<4.0.0,>=3.9")
    fake_python_releases = fake_release_set(package="python", releases=["3.9", "3.10", "3.11"])

    def fake_get_python_releases(python_specifiers: SpecifierSet) -> ReleaseSet:
        assert python_specifiers_ == python_specifiers
        return fake_python_releases

    monkeypatch.setattr("compreq.contexts.get_python_releases", fake_get_python_releases)

    fake_foobar_releases = fake_release_set(package="foo.bar", releases=["1.2.3", "1.2.4", "1.2.5"])

    def fake_get_pypi_releases(package: str) -> ReleaseSet:
        assert "foo.bar" == package
        return fake_foobar_releases

    monkeypatch.setattr("compreq.contexts.get_pypi_releases", fake_get_pypi_releases)

    context = DefaultContext(python_specifiers_, fake_now)
    assert fake_now == context.now
    assert fake_python_releases == context.releases("python")
    assert fake_foobar_releases == context.releases("foo.bar")

    pcontext = context.for_package("foo.bar")
    assert "foo.bar" == pcontext.package
    assert fake_now == pcontext.now
    assert fake_python_releases == pcontext.releases("python")
    assert fake_foobar_releases == pcontext.releases("foo.bar")
