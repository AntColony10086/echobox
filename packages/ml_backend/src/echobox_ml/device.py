"""Auto-select the best available torch device (cuda > mps > cpu)."""

from typing import Literal

DeviceName = Literal["cuda", "mps", "cpu"]


def _has_cuda() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except ImportError:
        return False


def _has_mps() -> bool:
    try:
        import torch  # noqa: PLC0415

        return bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    except ImportError:
        return False


def resolve_device(requested: str) -> DeviceName:
    if requested == "cpu":
        return "cpu"
    if requested == "cuda":
        return "cuda" if _has_cuda() else ("mps" if _has_mps() else "cpu")
    if requested == "mps":
        return "mps" if _has_mps() else "cpu"
    if _has_cuda():
        return "cuda"
    if _has_mps():
        return "mps"
    return "cpu"
