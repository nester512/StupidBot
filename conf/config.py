from typing import Optional
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base app
    LOG_LEVEL: str
    BOT_TOKEN: str
    WEBHOOK_URL: str | None

    # Retry configuration
    retry_max_retries: int = Field(3, env="RETRY_MAX_RETRIES")
    retry_base_delay: float = Field(0.5, env="RETRY_BASE_DELAY")
    retry_backoff: float = Field(2.0, env="RETRY_BACKOFF")
    retry_jitter: float = Field(0.25, env="RETRY_JITTER")
    retry_status_codes: str = Field("429,500,502,503,504", env="RETRY_STATUS_CODES")

    @property
    def retry_status_codes_set(self) -> set[int]:
        """Парсит строку статус кодов в множество интов."""
        return {int(code.strip()) for code in self.retry_status_codes.split(",") if code.strip()}

    model_config = SettingsConfigDict(
        env_file="./conf/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
