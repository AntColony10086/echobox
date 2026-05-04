"""Deterministic train/val/test split."""

import random

from echobox_app.domain.splits import SplitConfig, SplitName
from echobox_app.errors import ValidationError


def propose_split(
    image_filenames: list[str],
    train: float = 0.7,
    val: float = 0.15,
    test: float = 0.15,
    seed: int = 42,
) -> SplitConfig:
    if not image_filenames:
        raise ValidationError("cannot split empty image list")

    cfg = SplitConfig(train=train, val=val, test=test, seed=seed)
    if not cfg.is_valid():
        raise ValidationError(
            f"split ratios must sum to 1.0 (got {train + val + test})",
            detail={"train": train, "val": val, "test": test},
        )

    n = len(image_filenames)
    n_train = int(n * train)
    n_val = int(n * val)

    shuffled = list(image_filenames)
    rng = random.Random(seed)
    rng.shuffle(shuffled)

    assignments: dict[str, SplitName] = {}
    for i, fname in enumerate(shuffled):
        if i < n_train:
            assignments[fname] = "train"
        elif i < n_train + n_val:
            assignments[fname] = "val"
        else:
            assignments[fname] = "test"

    cfg.assignments = assignments
    return cfg
