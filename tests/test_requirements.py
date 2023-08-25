from packaging.requirements import Requirement

from compreq import RequirementSet


def test_requirement_set() -> None:
    requirement_1 = Requirement("foo_1")
    requirement_2 = Requirement("foo_2")
    requirement_set = RequirementSet.new([requirement_1, requirement_2])

    assert len(requirement_set) == 2
    assert {
        "foo_1": requirement_1,
        "foo_2": requirement_2,
    } == dict(requirement_set)
    assert "foo_1" in requirement_set
    assert requirement_1 == requirement_set["foo_1"]
    assert "foo_3" not in requirement_set
    assert bool(requirement_set)


def test_requirement_set__empty() -> None:
    requirement_set = RequirementSet.new([])

    assert len(requirement_set) == 0
    assert {} == dict(requirement_set)
    assert "foo_1" not in requirement_set
    assert not bool(requirement_set)
