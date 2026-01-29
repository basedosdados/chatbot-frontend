from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Website API settings
    WEBSITE_HOST: str = Field(description="basedosdados API host")
    WEBSITE_PORT: str = Field(description="basedosdados API port")

    @computed_field
    @property
    def BASE_WEBSITE_URL(self) -> str:
        return f"http://{self.WEBSITE_HOST}:{self.WEBSITE_PORT}"

    # Chatbot API settings
    CHATBOT_HOST: str = Field(description="chatbot API host")
    CHATBOT_PORT: str = Field(description="chatbot API port")

    @computed_field
    @property
    def BASE_CHATBOT_URL(self) -> str:
        return f"http://{self.CHATBOT_HOST}:{self.CHATBOT_PORT}"

    # Logging settings
    LOG_LEVEL: str = Field(
        default="INFO", description="The minimum severity level for logging messages."
    )
    LOG_BACKTRACE: bool = Field(
        default=True, description="Whether the full stacktrace should be displayed when an exception occur."
    )
    LOG_DIAGNOSE: bool = Field(
        default=False,
        description=(
            "Whether the exception trace should display the variables values to eases the debugging. "
            "This should be set to False in production to avoid leaking sensitive data."
        )
    )
    LOG_ENQUEUE: bool = Field(
        default=False,
        description=(
            "Whether the messages to be logged should first pass through a multiprocessing-safe queue before reaching the sink. "
            "This is useful while logging to a file through multiple processes and also has the advantage of making logging calls non-blocking."
        )
    )

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
