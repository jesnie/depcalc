from pathlib import Path
from unittest.mock import MagicMock

import pytest
from packaging.requirements import Requirement
from packaging.version import Version
from pytest import MonkeyPatch

import compreq as cr
from compreq.scripts import get_dist_metadata


@pytest.fixture(autouse=True)
def _mock_run(monkeypatch: MonkeyPatch) -> MagicMock:
    subprocess = MagicMock()
    monkeypatch.setattr("compreq.virtualenv.subprocess", subprocess)
    subprocess.run.return_value = MagicMock(returncode=0)
    subprocess.PIPE = "PIPE"
    subprocess.STDOUT = "STDOUT"
    return subprocess.run  # type: ignore[no-any-return]


def test_create_venv(_mock_run: MagicMock) -> None:
    cr.create_venv("/home/jesper/venv", "3.10.1")
    _mock_run.assert_called_once_with(
        "virtualenv -p python3.10 /home/jesper/venv",
        shell=True,
        check=False,
        stdout="PIPE",
        stderr="STDOUT",
    )


def test_remove_venv(tmp_path: Path) -> None:
    venv_path = tmp_path / "venv"
    venv_path.mkdir()
    (venv_path / "test.txt").touch()
    assert venv_path.exists()

    venv = cr.VirtualEnv(venv_path)

    cr.remove_venv(venv)

    assert not venv_path.exists()
    assert tmp_path.is_dir()


def test_temp_venv(_mock_run: MagicMock) -> None:
    # pylint: disable=protected-access

    with cr.temp_venv("3.10") as venv:
        path = venv._path
        assert path.exists()
        _mock_run.assert_called_once_with(
            f"virtualenv -p python3.10 {path}",
            shell=True,
            check=False,
            stdout="PIPE",
            stderr="STDOUT",
        )
    assert not path.exists()

    _mock_run.reset_mock()

    with pytest.raises(ValueError):
        with cr.temp_venv("3.10") as venv:
            path = venv._path
            assert path.exists()
            _mock_run.assert_called_once_with(
                f"virtualenv -p python3.10 {path}",
                shell=True,
                check=False,
                stdout="PIPE",
                stderr="STDOUT",
            )
            raise ValueError("test error")
    assert not path.exists()


def test_temp_venv__no_clean_on_error(_mock_run: MagicMock) -> None:
    # pylint: disable=protected-access

    with cr.temp_venv("3.10", clean_on_error=False) as venv:
        path = venv._path
        assert path.exists()
        _mock_run.assert_called_once_with(
            f"virtualenv -p python3.10 {path}",
            shell=True,
            check=False,
            stdout="PIPE",
            stderr="STDOUT",
        )
    assert not path.exists()

    _mock_run.reset_mock()

    with pytest.raises(ValueError):
        with cr.temp_venv("3.10", clean_on_error=False) as venv:
            path = venv._path
            assert path.exists()
            _mock_run.assert_called_once_with(
                f"virtualenv -p python3.10 {path}",
                shell=True,
                check=False,
                stdout="PIPE",
                stderr="STDOUT",
            )
            raise ValueError("test error")
    assert path.exists()


def test_virtual_env__run(_mock_run: MagicMock) -> None:
    _mock_run.return_value.stdout = b"Hello, world!"
    venv = cr.VirtualEnv("/home/jesper/venv")

    assert "Hello, world!" == venv.run("foo bar baz")

    _mock_run.assert_called_once_with(
        ". /home/jesper/venv/bin/activate && foo bar baz",
        shell=True,
        check=False,
        stdout="PIPE",
        stderr="STDOUT",
    )


def test_virtual_env__install(_mock_run: MagicMock) -> None:
    venv = cr.VirtualEnv("/home/jesper/venv")

    venv.install(
        cr.RequirementSet.new(
            [
                Requirement("foo>=1.2.3"),
                Requirement("bar<2.0,>=1.0"),
            ]
        )
    )

    _mock_run.assert_called_once_with(
        '. /home/jesper/venv/bin/activate && pip install "bar<2.0,>=1.0" "foo>=1.2.3"',
        shell=True,
        check=False,
        stdout="PIPE",
        stderr="STDOUT",
    )


def test_virtual_env__install__no_deps(_mock_run: MagicMock) -> None:
    venv = cr.VirtualEnv("/home/jesper/venv")

    venv.install(
        cr.RequirementSet.new(
            [
                Requirement("foo>=1.2.3"),
                Requirement("bar<2.0,>=1.0"),
            ]
        ),
        deps=False,
    )

    _mock_run.assert_called_once_with(
        '. /home/jesper/venv/bin/activate && pip install --no-deps "bar<2.0,>=1.0" "foo>=1.2.3"',
        shell=True,
        check=False,
        stdout="PIPE",
        stderr="STDOUT",
    )


def test_virtual_env__package_metadata(_mock_run: MagicMock) -> None:
    _mock_run.return_value.stdout = b"""{
  "name": "foo.bar",
  "version": "1.2.3",
  "requires_python": "<4.0,>=3.9",
  "requires": [
    "foo>=1.2.3",
    "bar<2.0,>=1.0"
  ]
}
"""

    venv = cr.VirtualEnv("/home/jesper/venv")
    assert cr.DistMetadata(
        package="foo.bar",
        version=Version("1.2.3"),
        requires=cr.RequirementSet.new(
            [
                Requirement("python<4.0,>=3.9"),
                Requirement("foo>=1.2.3"),
                Requirement("bar<2.0,>=1.0"),
            ]
        ),
    ) == venv.package_metadata("foo.bar")
    _mock_run.assert_called_once_with(
        f". /home/jesper/venv/bin/activate && python {get_dist_metadata.__file__} foo.bar",
        shell=True,
        check=False,
        stdout="PIPE",
        stderr="STDOUT",
    )
