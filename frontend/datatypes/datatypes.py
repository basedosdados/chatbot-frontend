import time
import uuid
from datetime import datetime
from typing import Iterator

from pydantic import BaseModel, Field, UUID4


class Thread(BaseModel):
    id: UUID4
    account: int
    title: str|None
    created_at: datetime

class UserMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str

class MessagePair(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    user_message: str
    assistant_message: str
    generated_queries: list[str] | None = Field(default=None)

    @property
    def stream_characters(self) -> Iterator[str]:
        """Streams the assistant message character by character

        Yields:
            Iterator[str]
        """
        for character in self.assistant_message:
            yield character
            time.sleep(0.01)

    @property
    def stream_words(self) -> Iterator[str]:
        """Streams the assistant message word by word

        Yields:
            Iterator[str]
        """
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
