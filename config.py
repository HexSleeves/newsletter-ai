"""Configuration settings for the newsletter backend."""

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings

# Claude Models
# claude-haiku-4-5-20251001 - $1 / MTokens
# claude-sonnet-4-5-20250929 - $3 / MTokens
# claude-opus-4-5-20251101 - $5 / MTokens

# OpenAI Models
# gpt-5-nano-2025-08-07 - $0.05
# gpt-5-mini-2025-08-07 - $0.25
# gpt-5.1-2025-11-13 - $1.25
# o4-mini-2025-04-16 - $1.10
# gpt-4.1-mini-2025-04-14 - $0.40


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
    llm_provider: LLMProvider = LLMProvider.OPENAI
    llm_model: str | None = None  # If not set, uses provider default

    # API Keys (optional - only needed for chosen provider)
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None
    openrouter_api_key: str | None = None
    z_ai_api_key: str | None = None

    # Email
    resend_api_key: str | None = None

    # Authentication
    admin_api_key: str = "change-me-in-production"

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
            LLMProvider.ANTHROPIC: "claude-haiku-4-5-20251001",
            LLMProvider.GEMINI: "gemini-2.5-flash",
            LLMProvider.OPENAI: "gpt-5-mini-2025-08-07",
            LLMProvider.OPENROUTER: "openrouter/bert-nebulon-alpha",
            LLMProvider.Z_AI: "glm-4.6",
        }
        return defaults[self.llm_provider]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
