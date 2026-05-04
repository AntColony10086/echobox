"""Agent chat message representation."""

from dataclasses import dataclass, field
from typing import Any, Literal

MessageRole = Literal["user", "assistant", "tool", "system"]
_VALID_ROLES = {"user", "assistant", "tool", "system"}


@dataclass
class Message:
    role: MessageRole
    content: str
    tool_call_id: str | None = None
    tool_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.role not in _VALID_ROLES:
            raise ValueError(f"invalid role: {self.role}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "tool_call_id": self.tool_call_id,
            "tool_name": self.tool_name,
            "metadata": dict(self.metadata),
        }
