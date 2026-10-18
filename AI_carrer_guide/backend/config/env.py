from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Career Mentor"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    falkordb_host: str = "localhost"
    falkordb_port: int = Field(default=6379, ge=1, le=65535)
    falkordb_username: str | None = None
    falkordb_password: str | None = None
    falkordb_graph_name: str = "career_mentor"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    unstop_scrape_url: str | None = None
    wemakedevs_scrape_url: str | None = None
    github_bounties_scrape_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
