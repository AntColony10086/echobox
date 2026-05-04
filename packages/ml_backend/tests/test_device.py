from unittest.mock import patch

from echobox_ml.device import resolve_device


def test_explicit_cpu_returns_cpu() -> None:
    assert resolve_device("cpu") == "cpu"


def test_explicit_cuda_returns_cuda_if_available() -> None:
    with patch("echobox_ml.device._has_cuda", return_value=True):
        assert resolve_device("cuda") == "cuda"


def test_explicit_cuda_falls_back_to_cpu_if_unavailable() -> None:
    with (
        patch("echobox_ml.device._has_cuda", return_value=False),
        patch("echobox_ml.device._has_mps", return_value=False),
    ):
        assert resolve_device("cuda") == "cpu"


def test_auto_picks_cuda_first() -> None:
    with (
        patch("echobox_ml.device._has_cuda", return_value=True),
        patch("echobox_ml.device._has_mps", return_value=True),
    ):
        assert resolve_device("auto") == "cuda"


def test_auto_picks_mps_when_no_cuda() -> None:
    with (
        patch("echobox_ml.device._has_cuda", return_value=False),
        patch("echobox_ml.device._has_mps", return_value=True),
    ):
        assert resolve_device("auto") == "mps"


def test_auto_falls_back_to_cpu() -> None:
    with (
        patch("echobox_ml.device._has_cuda", return_value=False),
        patch("echobox_ml.device._has_mps", return_value=False),
    ):
        assert resolve_device("auto") == "cpu"
