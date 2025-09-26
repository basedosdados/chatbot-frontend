import time
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import Any, Literal, Optional

from loguru import logger
from pydantic import UUID4, BaseModel, Field, model_validator

from frontend.utils import escape_currency


class Thread(BaseModel):
    id: UUID4
    account: int
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
    output: str
    metadata: dict[str, Any] | None = None

EventType = Literal[
    "tool_call",
    "tool_output",
    "final_answer",
    "error",
    "complete",
]

class EventData(BaseModel):
    run_id: Optional[UUID4] = None
    content: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    tool_outputs: Optional[list[ToolOutput]] = None
    error_details: Optional[dict[str, Any]] = None

class StreamEvent(BaseModel):
    type: EventType
    data: EventData

class MessagePair(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    user_message: str
    assistant_message: str|None = Field(default=None)
    error_message: str|None = Field(default=None)
    events: list[StreamEvent]

    @model_validator(mode="after")
    def validate_exactly_one_response(self) -> "MessagePair":
        if (self.assistant_message is not None) ^ (self.error_message is not None):
            return self
        raise ValueError(
            "Only one and exactly one of 'assistant_message' "
            "or 'error_message' fields must be provided"
        )

    @property
    def formatted_assistant_message(self) -> str | None:
        """Assistant message with currency symbols escaped for markdown rendering."""
        if self.assistant_message:
            try:
                return escape_currency(self.assistant_message)
            except Exception:
                logger.exception(f"Failed to escape currency in message pair {self.id}:")
        return self.assistant_message

    def stream_characters(self) -> Generator[str]:
        """Streams the assistant message character by character.

        Yields:
            Generator[str].
        """
        if self.assistant_message:
            for character in self.formatted_assistant_message:
                yield character
                time.sleep(0.01)

    def stream_words(self) -> Generator[str]:
        """Streams the assistant message word by word.

        Yields:
            Generator[str].
        """
        if self.assistant_message:
            for word in filter(None, self.formatted_assistant_message.split(" ")):
                yield word + " "
                time.sleep(0.02)
