"""SSE chat endpoint that drives LangGraph one turn per user message."""

import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from echobox_app.agent.graph import build_graph
from echobox_app.agent.state import AgentState
from echobox_app.api.deps import session_dep, settings_dep
from echobox_app.api.projects import _PALETTE
from echobox_app.config import AppSettings
from echobox_app.db.models import ChatMessage, Image, Label, Project
from echobox_app.domain.messages import Message
from echobox_app.errors import ProjectNotFound
from echobox_app.llm.factory import build_chat_model
from echobox_app.workspace.manager import WorkspaceManager

router = APIRouter(prefix="/api/projects", tags=["chat"])


class ChatPayload(BaseModel):
    content: str = Field(min_length=1)


@router.post("/{pid}/chat")
def chat(
    pid: int,
    payload: ChatPayload,
    session: Annotated[Session, Depends(session_dep)],
    settings: Annotated[AppSettings, Depends(settings_dep)],
) -> StreamingResponse:
    project = session.get(Project, pid)
    if project is None:
        raise ProjectNotFound(f"project {pid} not found", detail={"project_id": pid})

    db_messages = list(project.chat_messages)
    state = AgentState(
        project_id=pid,
        messages=[
            Message(
                role=m.role,
                content=m.content,
                tool_call_id=m.tool_call_id,
                tool_name=m.tool_name,
                # Re-hydrate metadata (tool_calls) from JSON column so the LLM sees
                # the full call→result chain across turns. MiniMax (and other strict
                # OpenAI-compatible providers) reject ToolMessage refs whose
                # matching tool_call wasn't present on the prior AssistantMessage.
                metadata=json.loads(m.metadata_json) if m.metadata_json else {},
            )
            for m in db_messages
        ],
        labels=[lbl.name for lbl in project.labels],
        export_format=project.export_format,
        status=project.status,  # type: ignore[arg-type]
    )
    state.messages.append(Message(role="user", content=payload.content))

    # WorkspaceManager appends "projects/{id}" to root internally, so root is just data_dir.
    workspace = WorkspaceManager(root=settings.data_dir, project_id=pid)
    workspace.init_directories()
    llm = build_chat_model(settings)
    graph = build_graph(llm)

    async def _stream() -> AsyncIterator[bytes]:
        result = graph.invoke({"state": state, "workspace": workspace})
        out_state: AgentState = result["state"]

        old_count = len(db_messages)
        new_messages = out_state.messages[old_count:]

        # 1) Persist all new chat messages (including metadata for tool_calls)
        for m in new_messages:
            session.add(
                ChatMessage(
                    project_id=pid,
                    role=m.role,
                    content=m.content,
                    tool_call_id=m.tool_call_id,
                    tool_name=m.tool_name,
                    metadata_json=(
                        json.dumps(m.metadata, ensure_ascii=False) if m.metadata else None
                    ),
                )
            )

        # 2) Sync mutated AgentState back into DB so refetch sees the changes.
        #    Without this, agent tools (set_labels, propose_split, etc.) modify
        #    only AgentState in memory; the cards never refresh.
        _sync_state_to_db(session, project, out_state, workspace)

        session.commit()

        # 3) Stream new messages back. Skip 'user' messages — frontend already
        #    appended the user turn optimistically when send() was called.
        for m in new_messages:
            if m.role == "user":
                continue
            event = {"type": "message", "data": m.to_dict()}
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode()
        yield b'data: {"type": "done"}\n\n'

    return StreamingResponse(_stream(), media_type="text/event-stream")


def _sync_state_to_db(
    session: Session,
    project: Project,
    state: AgentState,
    workspace: WorkspaceManager,
) -> None:
    """Mirror mutated AgentState fields back to the Project row + child tables."""
    # Source folder (in case agent re-pointed it)
    if state.folder_path is not None and state.folder_path != project.source_folder:
        project.source_folder = state.folder_path

    # Splits
    if state.splits is not None:
        project.train_ratio = state.splits.train
        project.val_ratio = state.splits.val
        project.test_ratio = state.splits.test
        project.split_seed = state.splits.seed

    # Export format
    if state.export_format is not None:
        project.export_format = state.export_format

    # Labels — append-only sync (we never delete from DB based on agent state)
    existing_label_names = {lbl.name for lbl in project.labels}
    palette_offset = len(project.labels)
    for idx, name in enumerate(state.labels):
        if name not in existing_label_names:
            session.add(
                Label(
                    project_id=project.id,
                    name=name,
                    color=_PALETTE[(palette_offset + idx) % len(_PALETTE)],
                )
            )

    # Images — sync from canonical_images (organize_images output)
    if state.canonical_images:
        existing_filenames = {img.filename for img in project.images}
        assignments = state.splits.assignments if state.splits else {}
        for idx, entry in enumerate(state.canonical_images):
            if entry.canonical in existing_filenames:
                continue
            split = assignments.get(entry.canonical, "train")
            # Use the SAME workspace.image_dir that organize_images wrote to,
            # so abs_path matches the actual file location on disk.
            session.add(
                Image(
                    project_id=project.id,
                    filename=entry.canonical,
                    abs_path=str((workspace.image_dir / entry.canonical).resolve()),
                    width=entry.width,
                    height=entry.height,
                    split=split,
                    index_in_project=idx,
                    source_path=str(entry.source),
                )
            )
