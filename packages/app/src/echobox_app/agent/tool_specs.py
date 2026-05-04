"""Tool specifications for LangGraph planner.

These wrap the deterministic tools in `echobox_app.tools` with metadata
the LLM uses to decide when/how to call them.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolSpec:
    name: str
    description: str
    args: dict[str, dict[str, Any]] = field(default_factory=dict)
    args_schema: dict[str, Any] | None = None


_SCAN_FOLDER = ToolSpec(
    name="scan_folder",
    description=(
        "Recursively scan a folder for image files. Returns counts, format "
        "distribution, and sample paths. Call this first when the user gives "
        "a folder path."
    ),
    args={"path": {"type": "string", "description": "absolute folder path"}},
    args_schema={"path": {"type": "string", "description": "absolute folder path"}},
)

_ORGANIZE_IMAGES = ToolSpec(
    name="organize_images",
    description=(
        "Copy valid images to the project workspace as 00001.<ext>, "
        "00002.<ext>, ... Writes mapping.json. Call after scan_folder succeeded."
    ),
    args={},
)

_PROPOSE_SPLIT = ToolSpec(
    name="propose_split",
    description=(
        "Deterministically split organized images into train/val/test by ratios. "
        "Default 0.7/0.15/0.15 with seed 42."
    ),
    args={
        "train": {"type": "number", "description": "train ratio 0..1"},
        "val": {"type": "number", "description": "val ratio 0..1"},
        "test": {"type": "number", "description": "test ratio 0..1"},
        "seed": {"type": "integer", "description": "random seed"},
    },
    args_schema={
        "train": {"type": "number", "description": "train ratio 0..1"},
        "val": {"type": "number", "description": "val ratio 0..1"},
        "test": {"type": "number", "description": "test ratio 0..1"},
        "seed": {"type": "integer", "description": "random seed"},
    },
)

_SET_LABELS = ToolSpec(
    name="set_labels",
    description="Set the project label set. Names must match ^[a-zA-Z0-9_-]+$.",
    args={
        "labels": {
            "type": "array",
            "items": {"type": "string"},
            "description": "label names",
        }
    },
    args_schema={
        "labels": {
            "type": "array",
            "items": {"type": "string"},
            "description": "label names",
        }
    },
)

_PROPOSE_LABELS = ToolSpec(
    name="propose_labels",
    description=(
        "Heuristic: if source folder has class-named subdirectories (e.g. "
        "source/positive/, source/negative/), suggest those names as labels. "
        "Otherwise returns empty and you should ask the user."
    ),
    args={},
)

_SET_EXPORT_FORMAT = ToolSpec(
    name="set_export_format",
    description="Lock the export format. One of: coco, yolo, voc, ls_json.",
    args={"fmt": {"type": "string", "enum": ["coco", "yolo", "voc", "ls_json"]}},
    args_schema={"fmt": {"type": "string", "enum": ["coco", "yolo", "voc", "ls_json"]}},
)

_FINALIZE_SETUP = ToolSpec(
    name="finalize_setup",
    description=(
        "Run critic validation. If all required state is set, transitions "
        "project to status=ready. Otherwise returns error list — fix and retry."
    ),
    args={},
)

TOOL_SPECS: list[ToolSpec] = [
    _SCAN_FOLDER,
    _ORGANIZE_IMAGES,
    _PROPOSE_SPLIT,
    _SET_LABELS,
    _PROPOSE_LABELS,
    _SET_EXPORT_FORMAT,
    _FINALIZE_SETUP,
]


def to_openai_function_specs() -> list[dict[str, Any]]:
    """Convert to OpenAI function-calling spec format."""
    out: list[dict[str, Any]] = []
    for spec in TOOL_SPECS:
        properties = {
            k: {kk: vv for kk, vv in v.items() if kk != "description"} for k, v in spec.args.items()
        }
        descriptions = {k: v.get("description", "") for k, v in spec.args.items()}
        for k, prop in properties.items():
            if descriptions[k]:
                prop["description"] = descriptions[k]
        out.append(
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": list(spec.args.keys()),
                    },
                },
            }
        )
    return out
