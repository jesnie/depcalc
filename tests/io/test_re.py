from pathlib import Path

from compreq import TextReFile


def test_text_re_file(tmp_path: Path) -> None:
    path = tmp_path / "test.txt"
    path.write_text(
        """
foo 123
bar 234
baz 345""",
        encoding="utf-8",
    )

    with TextReFile.open(path) as fp:
        assert 0 == fp.sub("test", "test")
        assert 2 == fp.sub("23", "xx")
    assert """
foo 1xx
bar xx4
baz 345""" == path.read_text(
        encoding="utf-8"
    )
