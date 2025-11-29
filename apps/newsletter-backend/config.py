"""Configuration settings for the newsletter backend."""

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    Z_AI = "z-ai"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    llm_provider: LLMProvider = LLMProvider.OPENROUTER
    llm_model: str | None = None  # If not set, uses provider default

    # API Keys (optional - only needed for chosen provider)
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None
    openrouter_api_key: str | None = None
    z_ai_api_key: str | None = None

    # Database
    database_url: str = "sqlite:///./newsletter.db"

    # RSS Feeds
    rss_feeds: str = "https://techcrunch.com/feed/,https://www.theverge.com/rss/index.xml"

    class Config:
        """Configuration settings for the newsletter backend."""

        env_file = ".env"
        case_sensitive = False

    @property
    def rss_feed_list(self) -> list[str]:
        """Parse comma-separated RSS feeds into a list."""
        return [feed.strip() for feed in self.rss_feeds.split(",") if feed.strip()]

    @property
    def default_model(self) -> str:
        """Get the default model for the configured provider."""
        if self.llm_model:
            return self.llm_model

        defaults = {
            LLMProvider.OPENAI: "gpt-4o",
            LLMProvider.GEMINI: "gemini-2.5-flash",
            LLMProvider.OPENROUTER: "openrouter/bert-nebulon-alpha",
            LLMProvider.ANTHROPIC: "claude-sonnet-4-20250514",
            LLMProvider.Z_AI: "glm-4.6",
        }
        return defaults[self.llm_provider]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
