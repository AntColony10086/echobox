import pytest
from echobox_ml.config import MLSettings


def test_ml_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ECHOBOX_ML_GECO2_WEIGHTS", raising=False)

    settings = MLSettings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 9090
    assert settings.device == "auto"
    assert settings.geco2_weights is None  # Plan 3 will require it
    assert settings.max_predictions_default == 200
    assert settings.score_threshold_default == 0.25


def test_ml_settings_device_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECHOBOX_ML_DEVICE", "cpu")

    settings = MLSettings(_env_file=None)

    assert settings.device == "cpu"
