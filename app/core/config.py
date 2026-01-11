from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_version: str = "0.1.0"
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_key: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    embedding_dimensions: int = 1536
    allowed_origins: str | List[str] = Field(default="*")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if value is None:
            return ["*"]
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            value = value.strip().strip("\"")
            if value == "":
                return ["*"]
            return [item.strip() for item in value.split(",") if item.strip()]
        return ["*"]


settings = Settings()
