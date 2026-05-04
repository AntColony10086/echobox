from echobox_mcp.server import ALL_TOOLS, build_server


def test_server_lists_3_tools() -> None:
    server = build_server()
    assert server.name == "echobox"
    assert len(ALL_TOOLS) == 3
    names = {t.name for t in ALL_TOOLS}
    assert names == {
        "start_annotation_project",
        "search_annotations",
        "export_dataset",
    }
