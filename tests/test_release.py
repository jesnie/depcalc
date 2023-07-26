import datetime as dt

from packaging.version import Version

from depcalc.release import (
    Release,
    ReleaseSet,
    infer_and_set_successor,
    infer_successor,
)


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
    before_r220a2dev1 = Release(
        package="depcalc",
        version=Version("2.2.0a2dev1"),
        released_time=dt.datetime(2023, 8, 9, 12, 37),
        successor=None,
    )
    before_r220a1 = Release(
        package="depcalc",
        version=Version("2.2.0a1"),
        released_time=dt.datetime(2023, 8, 9, 12, 36),
        successor=None,
    )
    before_r210 = Release(
        package="depcalc",
        version=Version("2.1.0"),
        released_time=dt.datetime(2023, 8, 9, 12, 35),
        successor=None,
    )
    before_r210a2 = Release(
        package="depcalc",
        version=Version("2.1.0a2"),
        released_time=dt.datetime(2023, 8, 9, 12, 34),
        successor=None,
    )
    before_r210a2dev1 = Release(
        package="depcalc",
        version=Version("2.1.0a2dev1"),
        released_time=dt.datetime(2023, 8, 9, 12, 33),
        successor=None,
    )
    before_r210a1 = Release(
        package="depcalc",
        version=Version("2.1.0a1"),
        released_time=dt.datetime(2023, 8, 9, 12, 32),
        successor=None,
    )
    before_r200 = Release(
        package="depcalc",
        version=Version("2.0.0"),
        released_time=dt.datetime(2023, 8, 9, 12, 31),
        successor=None,
    )
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

    after_r220a2dev1 = Release(
        package="depcalc",
        version=Version("2.2.0a2dev1"),
        released_time=dt.datetime(2023, 8, 9, 12, 37),
        successor=None,
    )
    after_r220a1 = Release(
        package="depcalc",
        version=Version("2.2.0a1"),
        released_time=dt.datetime(2023, 8, 9, 12, 36),
        successor=None,
    )
    after_r210 = Release(
        package="depcalc",
        version=Version("2.1.0"),
        released_time=dt.datetime(2023, 8, 9, 12, 35),
        successor=None,
    )
    after_r210a2 = Release(
        package="depcalc",
        version=Version("2.1.0a2"),
        released_time=dt.datetime(2023, 8, 9, 12, 34),
        successor=after_r210,
    )
    after_r210a2dev1 = Release(
        package="depcalc",
        version=Version("2.1.0a2dev1"),
        released_time=dt.datetime(2023, 8, 9, 12, 33),
        successor=after_r210a2,
    )
    after_r210a1 = Release(
        package="depcalc",
        version=Version("2.1.0a1"),
        released_time=dt.datetime(2023, 8, 9, 12, 32),
        successor=after_r210a2,
    )
    after_r200 = Release(
        package="depcalc",
        version=Version("2.0.0"),
        released_time=dt.datetime(2023, 8, 9, 12, 31),
        successor=after_r210,
    )
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
