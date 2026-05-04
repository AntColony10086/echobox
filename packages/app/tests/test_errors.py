from echobox_app.errors import (
    ArisError,
    LLMUnavailable,
    MLBackendUnavailable,
    ProjectNotFound,
    ValidationError,
)


def test_base_error_has_code_and_status() -> None:
    err = ArisError("something broke")

    assert err.code == "internal_error"
    assert err.http_status == 500
    assert str(err) == "something broke"


def test_project_not_found_404() -> None:
    err = ProjectNotFound("project 7 missing")

    assert err.code == "project_not_found"
    assert err.http_status == 404


def test_ml_backend_unavailable_503() -> None:
    err = MLBackendUnavailable("ml_backend down")

    assert err.code == "ml_backend_unavailable"
    assert err.http_status == 503


def test_llm_unavailable_503() -> None:
    err = LLMUnavailable("dashscope timed out")

    assert err.code == "llm_unavailable"
    assert err.http_status == 503


def test_validation_error_400() -> None:
    err = ValidationError("bad bbox")

    assert err.code == "validation_failed"
    assert err.http_status == 400


def test_can_attach_detail() -> None:
    err = ProjectNotFound("not found", detail={"project_id": 99})

    assert err.detail == {"project_id": 99}
