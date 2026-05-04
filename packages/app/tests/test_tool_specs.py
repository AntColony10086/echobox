from echobox_app.agent.tool_specs import TOOL_SPECS


def test_all_tools_present() -> None:
    names = {t.name for t in TOOL_SPECS}
    assert names == {
        "scan_folder",
        "organize_images",
        "propose_split",
        "set_labels",
        "propose_labels",
        "set_export_format",
        "finalize_setup",
    }


def test_each_tool_has_description_and_args_schema() -> None:
    for spec in TOOL_SPECS:
        assert spec.description, f"{spec.name} missing description"
        assert spec.args_schema is not None or spec.args == {}, f"{spec.name} missing schema"


def test_scan_folder_signature() -> None:
    spec = next(t for t in TOOL_SPECS if t.name == "scan_folder")
    assert "path" in spec.args
