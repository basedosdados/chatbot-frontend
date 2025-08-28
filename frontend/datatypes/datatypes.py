import time
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import UUID4, BaseModel, Field, model_validator


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
    generated_queries: list[str] | None = Field(default=None)
    events: list[StreamEvent]|None

    @model_validator(mode="after")
    def validate_exactly_one_response(self) -> "MessagePair":
        if (self.assistant_message is not None) ^ (self.error_message is not None):
            return self
        raise ValueError(
            "Only one and exactly one of 'assistant_message' "
            "or 'error_message' fields must be provided"
        )

    @property
    def safe_events(self) -> list[StreamEvent]:
        return self.events or []

    @property
    def stream_characters(self) -> Generator[str]:
        """Streams the assistant message character by character

        Yields:
            Generator[str]
        """
        if self.assistant_message:
            for character in self.assistant_message:
                yield character
                time.sleep(0.01)

    @property
    def stream_words(self) -> Generator[str]:
        """Streams the assistant message word by word

        Yields:
            Generator[str]
        """
        if self.assistant_message:
            for word in filter(None, self.assistant_message.split(" ")):
                yield word + " "
                time.sleep(0.02)

    @property
    def formatted_sql_queries(self) -> str | None:
        """Generated SQL queries formatted as markdown code blocks

        Returns:
            str | None
        """
        if self.generated_queries is not None:
            return "\n".join([
                f"```sql\n{sql_query}\n```"
                for sql_query in self.generated_queries
            ])
        return None
