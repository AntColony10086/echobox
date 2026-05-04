import pytest
from echobox_app.tools.splits import propose_split


def test_split_assigns_all_images() -> None:
    images = [f"{i:05d}.jpg" for i in range(1, 11)]

    sc = propose_split(images, train=0.7, val=0.15, test=0.15, seed=42)

    assert len(sc.assignments) == 10
    assert all(s in {"train", "val", "test"} for s in sc.assignments.values())


def test_split_deterministic_seed() -> None:
    images = [f"{i:05d}.jpg" for i in range(1, 21)]

    a = propose_split(images, train=0.6, val=0.2, test=0.2, seed=42)
    b = propose_split(images, train=0.6, val=0.2, test=0.2, seed=42)

    assert a.assignments == b.assignments


def test_split_different_seed_different_result() -> None:
    images = [f"{i:05d}.jpg" for i in range(1, 21)]

    a = propose_split(images, train=0.5, val=0.25, test=0.25, seed=1)
    b = propose_split(images, train=0.5, val=0.25, test=0.25, seed=2)

    assert a.assignments != b.assignments


def test_split_proportions_approx() -> None:
    images = [f"{i:05d}.jpg" for i in range(1, 1001)]

    sc = propose_split(images, train=0.7, val=0.15, test=0.15, seed=42)
    counts = {"train": 0, "val": 0, "test": 0}
    for s in sc.assignments.values():
        counts[s] += 1

    assert abs(counts["train"] - 700) <= 10
    assert abs(counts["val"] - 150) <= 10
    assert abs(counts["test"] - 150) <= 10


def test_split_invalid_ratios_raise() -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        propose_split(["a.jpg"], train=0.5, val=0.3, test=0.3, seed=42)


def test_split_empty_images_raises() -> None:
    from echobox_app.errors import ValidationError

    with pytest.raises(ValidationError):
        propose_split([], train=0.7, val=0.15, test=0.15, seed=42)
