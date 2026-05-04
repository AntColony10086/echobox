def test_can_import_echobox_ml() -> None:
    import echobox_ml

    assert echobox_ml.__version__ == "0.0.1"
