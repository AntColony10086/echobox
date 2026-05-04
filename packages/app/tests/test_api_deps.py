from echobox_app.api.deps import get_settings, get_workspace_root


def test_get_settings_from_app(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    from echobox_app.main import create_app

    app = create_app()
    settings = get_settings(app)

    # The accessor wires to app.state correctly; the actual value depends on
    # whatever .env / env vars the host has set. Just verify the attribute is reachable.
    assert isinstance(settings.llm_model, str)
    assert settings.llm_model  # non-empty


def test_get_workspace_root_uses_data_dir(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ECHOBOX_APP_LLM_API_KEY", "stub")
    monkeypatch.setenv("ECHOBOX_APP_DATA_DIR", str(tmp_path))
    from echobox_app.config import AppSettings

    settings = AppSettings(_env_file=None)

    root = get_workspace_root(settings)

    assert root == tmp_path / "projects"
