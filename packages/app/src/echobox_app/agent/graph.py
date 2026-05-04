"""LangGraph wiring: planner LLM + tool executor loop, with iteration cap.

For v1 we use a hand-rolled state machine (not langgraph.StateGraph) because:
- The graph is linear (planner -> executor -> planner)
- Direct loop is easier to test deterministically
- We can swap to StateGraph later without API changes

Public API: build_graph(llm) -> object with .invoke({state, workspace}) -> dict.
"""

from dataclasses import dataclass
from typing import Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.messages import ToolMessage as LCToolMessage

from echobox_app.agent.executor import execute_tool
from echobox_app.agent.state import AgentState
from echobox_app.agent.tool_specs import to_openai_function_specs
from echobox_app.domain.messages import Message
from echobox_app.workspace.manager import WorkspaceManager

_SYSTEM_PROMPT = """You are an annotation project setup assistant.
Your job: help the user prepare a dataset for annotation.

You have these tools:
- scan_folder(path): scan a folder for image files
- organize_images(): copy valid images into the project workspace
- propose_split(train, val, test, seed): assign train/val/test splits
- set_labels(labels): set the label set
- propose_labels(): suggest labels from source folder structure
- set_export_format(fmt): pick coco/yolo/voc/ls_json
- finalize_setup(): validate and lock the project as ready

The user can also edit cards directly (you'll see SystemMessages reflecting their edits).

Be concise. Ask one thing at a time. Confirm before destructive actions.
When everything is set, call finalize_setup."""


class _Inputs(TypedDict):
    state: AgentState
    workspace: WorkspaceManager


@dataclass
class _CompiledGraph:
    llm: Any
    max_iterations: int

    def invoke(self, inputs: _Inputs) -> dict[str, Any]:
        state = inputs["state"]
        workspace = inputs["workspace"]
        bound_llm = self.llm.bind_tools(to_openai_function_specs())

        for _iteration in range(self.max_iterations):
            lc_messages = _to_lc_messages(state.messages)
            response: AIMessage = bound_llm.invoke(lc_messages)

            tool_calls = getattr(response, "tool_calls", []) or []
            _content = str(response.content) if response.content else ""
            if not tool_calls:
                state.messages.append(Message(role="assistant", content=_content))
                return {"state": state}

            state.messages.append(
                Message(
                    role="assistant",
                    content=_content,
                    metadata={
                        "tool_calls": [
                            {"id": tc["id"], "name": tc["name"], "args": tc["args"]}
                            for tc in tool_calls
                        ]
                    },
                )
            )

            for tc in tool_calls:
                result = execute_tool(state, workspace, tc["name"], tc["args"])
                state.messages.append(
                    Message(
                        role="tool",
                        content=str(result),
                        tool_call_id=tc["id"],
                        tool_name=tc["name"],
                    )
                )

        state.messages.append(
            Message(
                role="system",
                content=f"iteration limit reached ({self.max_iterations})",
            )
        )
        return {"state": state}


def build_graph(llm: Any, max_iterations: int = 8) -> _CompiledGraph:
    return _CompiledGraph(llm=llm, max_iterations=max_iterations)


def _to_lc_messages(messages: list[Message]) -> list[BaseMessage]:
    out: list[BaseMessage] = [SystemMessage(content=_SYSTEM_PROMPT)]
    for m in messages:
        if m.role == "user":
            out.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            # Re-attach tool_calls so the LLM sees the linkage to subsequent ToolMessages.
            # Some providers (e.g. MiniMax) reject tool_call_id refs without the matching
            # tool_call announcement. Stored in m.metadata["tool_calls"] by the planner.
            tool_calls = m.metadata.get("tool_calls", []) if m.metadata else []
            out.append(AIMessage(content=m.content, tool_calls=tool_calls))
        elif m.role == "tool":
            out.append(
                LCToolMessage(
                    content=m.content,
                    tool_call_id=m.tool_call_id or "",
                )
            )
        elif m.role == "system":
            out.append(SystemMessage(content=m.content))
    return out
