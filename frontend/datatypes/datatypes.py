import time
import uuid
from datetime import datetime
from typing import Any, Iterator, Literal

from pydantic import BaseModel, Field


class Thread(BaseModel):
    id: uuid.UUID
    account: int
    created_at: datetime

class UserMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str

class ChartData(BaseModel):
    data: list[dict[str, Any]] | None = Field(description="Preprocessed data", default=None)
    reasoning: str | None = Field(description="Brief explanation of how the query results were processed, including any assumptions made, conflicts resolved, or placeholders used", default=None)

class ChartMetadata(BaseModel):
    chart_type: Literal["bar", "horizontal_bar", "line", "pie", "scatter"] | None = Field(description="Name of the chart type", default=None)
    title: str | None = Field(description="Title of the chart", default=None)
    x_axis: str | None = Field(description="Name of the variable to be plotted on the x-axis", default=None)
    x_axis_title: str | None = Field(description="Human friendly label for the x-axis", default=None)
    y_axis: str | None = Field(description="Name of the variable to be plotted on the y-axis", default=None)
    y_axis_title: str | None = Field(description="Human friendly label for the y-axis", default=None)
    label: str | None = Field(description="Name of the variable to be used as label", default=None)
    label_title: str | None = Field(description="Human friendly name for the label", default=None)
    reasoning: str | None = Field(description="Brief explanation for your recommendation", default=None)

    @property
    def valid_label(self) -> str | None:
        if self.label == self.x_axis \
        or self.label == self.y_axis:
            return None
        else:
            return self.label

class Chart(BaseModel):
    data: ChartData
    metadata: ChartMetadata
    is_valid: bool

class MessagePair(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    thread: uuid.UUID
    model_uri: str
    user_message: str
    assistant_message: str
    generated_queries: list[str] | None = Field(default=None)
    generated_chart: Chart | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)

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

    @property
    def chart_data(self) -> ChartData | None:
        """The ChartData object

        Returns:
            ChartData | None
        """
        if self.generated_chart is not None:
            return self.generated_chart.data
        return None

    @property
    def chart_metadata(self) -> ChartMetadata | None:
        """The ChartMetadata object

        Returns:
            ChartMetadata | None
        """
        if self.generated_chart is not None:
            return self.generated_chart.metadata
        return None

    @property
    def has_chart(self) -> bool:
        """Whether the ChatInteraction contains a non-empty Chart object

        Returns:
            bool
        """
        has_data = self.generated_chart and self.generated_chart.data.data
        has_metadata = self.generated_chart and self.generated_chart.metadata.chart_type
        return has_data and has_metadata

    @property
    def has_valid_chart(self) -> bool:
        """Whether the ChatInteraction contains a Chart object with a valid chart

        Returns:
            bool
        """
        if self.has_chart:
            return self.generated_chart.is_valid
        return False
