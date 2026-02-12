import re
import time
import uuid
from collections.abc import Generator
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from loguru import logger
from pydantic import UUID4, BaseModel, ConfigDict, Field, JsonValue, field_validator


class Thread(BaseModel):
    id: UUID4
    user_id: UUID4
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
    artifacts: list = Field(default_factory=list)
    events: list[StreamEvent] = Field(default_factory=list)
    status: MessageStatus

    @field_validator("artifacts", "events", mode="before")
    @classmethod
    def ensure_list(cls, value: list | None) -> list:
        return value if value is not None else []

    @property
    def formatted_content(self) -> str | None:
        """Assistant message with currency symbols escaped for markdown rendering."""
        if self.content:
            try:
                return self._escape_currency(self.content)
            except Exception:
                logger.exception(
                    f"Failed to escape currency symbols for message pair {self.id}:"
                )
        return self.content

    def _escape_currency(self, text: str):
        """Escape currency dollar signs ($) while preserving markdown math expressions.

        Args:
            text (str): Input text.

        Returns:
            str: Text with currency dollar signs escaped.
        """
        # Regex to match math blocks ($$...$$), inline math ($...$), or single dollars ($)
        # Inline math must not contain white spaces at the beginning/end of the expression
        pattern = r"(\$\$[\s\S]*?\$\$)|(\$(?!\$)(?!\s)[^\$\n]*?[^\$\s]\$)|(\$)"

        def repl(match: re.Match):
            if match.group(1):
                return match.group(1)
            elif match.group(2):
                return match.group(2)
            else:
                return r"\$"

        return re.sub(pattern, repl, text)

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
