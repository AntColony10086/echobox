from echobox_mcp.config import MCPSettings


def test_mcp_settings_defaults() -> None:
    settings = MCPSettings(_env_file=None)

    assert settings.app_url == "http://localhost:8000"
    assert settings.app_request_timeout_s == 60.0
    assert settings.transport == "stdio"
    assert settings.sse_port == 9100
