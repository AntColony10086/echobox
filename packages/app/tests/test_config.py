import pytest
from echobox_app.config import AppSettings
from pydantic import SecretStr


def test_settings_load_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "sk-test-123")

    settings = AppSettings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.db_url == "sqlite:///.data/projects.db"
    assert settings.llm_model == "qwen-plus"
    assert isinstance(settings.llm_api_key, SecretStr)
    assert settings.llm_api_key.get_secret_value() == "sk-test-123"


def test_settings_missing_api_key_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ECHOBOX_APP_LLM_API_KEY", raising=False)

    with pytest.raises(ValueError):
        AppSettings(_env_file=None)


def test_settings_overrides_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "sk-x")
    monkeypatch.setenv("ECHOBOX_APP_PORT", "9000")
    monkeypatch.setenv("ECHOBOX_APP_LLM_MODEL", "qwen-max")

    settings = AppSettings(_env_file=None)

    assert settings.port == 9000
    assert settings.llm_model == "qwen-max"
