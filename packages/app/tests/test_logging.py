import json

import structlog
from echobox_app.logging import configure_logging


def test_configure_pretty_does_not_raise() -> None:
    configure_logging(level="INFO", fmt="pretty")
    log = structlog.get_logger("test")
    log.info("hello", foo="bar")  # should not raise


def test_configure_json_emits_json(capsys) -> None:  # type: ignore[no-untyped-def]
    configure_logging(level="DEBUG", fmt="json")
    log = structlog.get_logger("test")
    log.info("hello", foo="bar")
    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["event"] == "hello"
    assert payload["foo"] == "bar"
    assert payload["level"] == "info"
