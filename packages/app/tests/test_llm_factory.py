from echobox_app.config import AppSettings
from echobox_app.llm.factory import build_chat_model
from langchain_openai import ChatOpenAI


def test_build_chat_model_returns_chat_openai(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "sk-stub")
    settings = AppSettings(_env_file=None)

    model = build_chat_model(settings)

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "qwen-plus"


def test_build_chat_model_overrides(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "sk-x")
    monkeypatch.setenv("ECHOBOX_APP_LLM_MODEL", "qwen-max")
    monkeypatch.setenv("ECHOBOX_APP_LLM_BASE_URL", "https://example.com/v1")
    settings = AppSettings(_env_file=None)

    model = build_chat_model(settings)

    assert model.model_name == "qwen-max"
    assert str(model.openai_api_base) == "https://example.com/v1"
