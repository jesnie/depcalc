from packaging.version import Version

from depcalc.release import ReleaseSet, infer_and_set_successor, infer_successor
from tests.utils import fake_release


def test_infer_successor() -> None:
    versions = [
        Version("2.0.0"),
        Version("2.1.0a1"),
        Version("2.1.0a2.dev0"),
        Version("2.1.0a2.dev0+local"),
        Version("2.1.0a2.dev1"),
        Version("2.1.0a2"),
        Version("2.1.0b1"),
        Version("2.1.0b2"),
        Version("2.1.0rc1"),
        Version("2.1.0rc2"),
        Version("2.1.0"),
        Version("2.1.0.post0"),
        Version("2.1.0.post1"),
        Version("3.0.0"),
        Version("1!1.0.0"),
        Version("1!1.1.0a1"),
        Version("1!1.1.0a2.dev0"),
    ]

    assert {
        Version("2.0.0"): Version("2.1.0"),
        Version("2.1.0a1"): Version("2.1.0a2"),
        Version("2.1.0a2.dev0"): Version("2.1.0a2.dev0+local"),
        Version("2.1.0a2.dev0+local"): Version("2.1.0a2.dev1"),
        Version("2.1.0a2.dev1"): Version("2.1.0a2"),
        Version("2.1.0a2"): Version("2.1.0b1"),
        Version("2.1.0b1"): Version("2.1.0b2"),
        Version("2.1.0b2"): Version("2.1.0rc1"),
        Version("2.1.0rc1"): Version("2.1.0rc2"),
        Version("2.1.0rc2"): Version("2.1.0"),
        Version("2.1.0"): Version("2.1.0.post0"),
        Version("2.1.0.post0"): Version("2.1.0.post1"),
        Version("2.1.0.post1"): Version("3.0.0"),
        Version("3.0.0"): Version("1!1.0.0"),
        Version("1!1.0.0"): None,
        Version("1!1.1.0a1"): None,
        Version("1!1.1.0a2.dev0"): None,
    } == infer_successor(versions)


def test_infer_superseded() -> None:
    before_r220a2dev1 = fake_release(version="2.2.0a2dev1", successor=None)
    before_r220a1 = fake_release(version="2.2.0a1", successor=None)
    before_r210 = fake_release(version="2.1.0", successor=None)
    before_r210a2 = fake_release(version="2.1.0a2", successor=None)
    before_r210a2dev1 = fake_release(version="2.1.0a2dev1", successor=None)
    before_r210a1 = fake_release(version="2.1.0a1", successor=None)
    before_r200 = fake_release(version="2.0.0", successor=None)
    before = ReleaseSet(
        "depcalc",
        {
            before_r200,
            before_r210a1,
            before_r210a2dev1,
            before_r210a2,
            before_r210,
            before_r220a1,
            before_r220a2dev1,
        },
    )

    after_r220a2dev1 = fake_release(version="2.2.0a2dev1", successor=None)
    after_r220a1 = fake_release(version="2.2.0a1", successor=None)
    after_r210 = fake_release(version="2.1.0", successor=None)
    after_r210a2 = fake_release(version="2.1.0a2", successor=after_r210)
    after_r210a2dev1 = fake_release(version="2.1.0a2dev1", successor=after_r210a2)
    after_r210a1 = fake_release(version="2.1.0a1", successor=after_r210a2)
    after_r200 = fake_release(version="2.0.0", successor=after_r210)
    after = ReleaseSet(
        "depcalc",
        {
            after_r200,
            after_r210a1,
            after_r210a2dev1,
            after_r210a2,
            after_r210,
            after_r220a1,
            after_r220a2dev1,
        },
    )

    assert after == infer_and_set_successor(before)
