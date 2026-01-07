import time
import uuid
from collections.abc import Generator
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from loguru import logger
from pydantic import UUID4, BaseModel, ConfigDict, Field, JsonValue

from frontend.utils import escape_currency


class Thread(BaseModel):
    id: UUID4
    user_id: int
    title: str
    created_at: datetime


class UserMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str


class ToolCall(BaseModel):
    id: str
    name: str
    args: dict[str, Any]


class ToolOutput(BaseModel):
    status: Literal["error", "success"]
    tool_call_id: str
    tool_name: str
    content: str = Field(validation_alias="output")
    artifact: JsonValue | None = None
    metadata: JsonValue | None = None

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
    )

EventType = Literal[
    "tool_call",
    "tool_output",
    "final_answer",
    "error",
    "complete",
]


class EventData(BaseModel):
    run_id: UUID4 | None = None
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_outputs: list[ToolOutput] | None = None
    error_details: dict[str, Any] | None = None


class StreamEvent(BaseModel):
    type: EventType
    data: EventData


class MessageRole(str, Enum):
    ASSISTANT = "ASSISTANT"
    USER = "USER"


class MessageStatus(str, Enum):
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class Message(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    role: MessageRole
    content: str
    artifacts: list | None
    events: list[StreamEvent] | None
    status: MessageStatus

    @property
    def formatted_content(self) -> str | None:
        """Assistant message with currency symbols escaped for markdown rendering."""
        if self.content:
            try:
                return escape_currency(self.content)
            except Exception:
                logger.exception(f"Failed to escape currency symbols for message pair {self.id}:")
        return self.content

    def stream_characters(self) -> Generator[str]:
        """Streams the assistant message character by character.

        Yields:
            Generator[str].
        """
        if self.content:
            for character in self.formatted_content:
                yield character
                time.sleep(0.01)

    def stream_words(self) -> Generator[str]:
        """Streams the assistant message word by word.

        Yields:
            Generator[str].
        """
        if self.content:
            for word in filter(None, self.formatted_content.split(" ")):
                yield word + " "
                time.sleep(0.02)
