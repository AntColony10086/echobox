"""Dispatch a single tool call: validate inputs, run the tool, mutate AgentState."""

from pathlib import Path
from typing import Any

from echobox_app.agent.state import AgentState
from echobox_app.errors import ArisError, ValidationError
from echobox_app.tools.filesystem import organize_images, scan_folder
from echobox_app.tools.labels import propose_labels, set_labels
from echobox_app.tools.project import finalize_setup, set_export_format
from echobox_app.tools.splits import propose_split
from echobox_app.workspace.manager import WorkspaceManager


def execute_tool(
    state: AgentState,
    workspace: WorkspaceManager,
    name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    try:
        if name == "scan_folder":
            return _do_scan(state, arguments)
        if name == "organize_images":
            return _do_organize(state, workspace)
        if name == "propose_split":
            return _do_propose_split(state, arguments)
        if name == "set_labels":
            return _do_set_labels(state, arguments)
        if name == "propose_labels":
            return _do_propose_labels(state)
        if name == "set_export_format":
            return _do_set_export_format(state, arguments)
        if name == "finalize_setup":
            return _do_finalize(state, workspace)
        return {"ok": False, "error": f"unknown tool: {name}", "code": "unknown_tool"}
    except ArisError as e:
        return {"ok": False, "error": e.message, "code": e.code, "detail": e.detail}


def _do_scan(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    path = args.get("path")
    if not path:
        raise ValidationError("path argument required")
    res = scan_folder(Path(path))
    state.folder_path = str(res.folder)
    state.inventory = res.inventory
    return {"ok": True, "data": res.to_dict()}


def _do_organize(state: AgentState, workspace: WorkspaceManager) -> dict[str, Any]:
    if state.inventory is None or state.folder_path is None:
        raise ValidationError("call scan_folder first")
    from echobox_app.domain.inventory import ScanResult

    sr = ScanResult(folder=Path(state.folder_path), inventory=state.inventory)
    res = organize_images(sr, workspace)
    state.canonical_images = list(res.entries)
    return {"ok": True, "data": {"copied_count": res.copied_count}}


def _do_propose_split(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    if not state.canonical_images:
        raise ValidationError("call organize_images first")
    cfg = propose_split(
        [e.canonical for e in state.canonical_images],
        train=float(args.get("train", 0.7)),
        val=float(args.get("val", 0.15)),
        test=float(args.get("test", 0.15)),
        seed=int(args.get("seed", 42)),
    )
    state.splits = cfg
    return {"ok": True, "data": cfg.to_dict()}


def _do_set_labels(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    labels = args.get("labels")
    if not isinstance(labels, list):
        raise ValidationError("labels must be a list of strings")
    out = set_labels(labels)
    state.labels = out
    return {"ok": True, "data": {"labels": out}}


def _do_propose_labels(state: AgentState) -> dict[str, Any]:
    if state.folder_path is None:
        raise ValidationError("call scan_folder first")
    suggestions = propose_labels(Path(state.folder_path))
    return {"ok": True, "data": {"suggestions": suggestions}}


def _do_set_export_format(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    fmt = args.get("fmt")
    if not isinstance(fmt, str):
        raise ValidationError("fmt argument required")
    state.export_format = set_export_format(fmt)
    return {"ok": True, "data": {"fmt": state.export_format}}


def _do_finalize(state: AgentState, workspace: WorkspaceManager) -> dict[str, Any]:
    res = finalize_setup(state)
    state.last_critic_errors = list(res.errors)
    if res.success:
        state.status = "ready"
        if state.splits is not None and state.inventory is not None:
            workspace.write_splits(state.splits)
            workspace.write_project_meta(
                {
                    "id": state.project_id,
                    "status": "ready",
                    "labels": state.labels,
                    "export_format": state.export_format,
                    "splits": {
                        "train": state.splits.train,
                        "val": state.splits.val,
                        "test": state.splits.test,
                        "seed": state.splits.seed,
                    },
                    "image_count": len(state.canonical_images),
                }
            )
        return {"ok": True, "data": {"status": "ready"}}
    return {
        "ok": False,
        "error": "critic failed",
        "code": "critic_failed",
        "detail": {"errors": res.errors},
    }
