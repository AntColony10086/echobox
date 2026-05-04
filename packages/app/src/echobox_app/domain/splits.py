"""Train/val/test split configuration and assignment."""

from dataclasses import dataclass, field
from typing import Any, Literal

SplitName = Literal["train", "val", "test"]


@dataclass
class SplitConfig:
    train: float
    val: float
    test: float
    seed: int = 42
    assignments: dict[str, SplitName] = field(default_factory=dict)

    def is_valid(self, tol: float = 1e-6) -> bool:
        total = self.train + self.val + self.test
        return abs(total - 1.0) < tol and all(r >= 0 for r in (self.train, self.val, self.test))

    def to_dict(self) -> dict[str, Any]:
        return {
            "train": self.train,
            "val": self.val,
            "test": self.test,
            "seed": self.seed,
            "assignments": dict(self.assignments),
        }


@dataclass
class SplitResult:
    config: SplitConfig

    def to_dict(self) -> dict[str, Any]:
        return self.config.to_dict()
