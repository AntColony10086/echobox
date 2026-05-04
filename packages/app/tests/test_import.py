def test_can_import_echobox_app() -> None:
    import echobox_app

    assert echobox_app.__version__ == "0.0.1"
