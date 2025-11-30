"""LLM provider abstraction and utilities."""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.logging_config import get_logger
from config import LLMProvider, get_settings

logger = get_logger(__name__)


class LLMError(Exception):
    """Raised when LLM operations fail after retries."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=True,
)
async def _retry_llm_call(llm: BaseChatModel, messages: list) -> str:
    """Retry LLM calls with exponential backoff.

    Args:
        llm: LLM instance
        messages: List of messages to send

    Returns:
        LLM response content

    Raises:
        LLMError: If all retry attempts fail
    """
    try:
        response = await llm.ainvoke(messages)
        if not response or not response.content:
            raise ValueError("Empty response from LLM")
        return response.content
    except Exception as e:
        logger.error("LLM call failed: %s", str(e))
        raise


def get_llm() -> BaseChatModel:
    """Get the configured LLM instance with retry logic."""
    settings = get_settings()
    model = settings.default_model

    try:
        match settings.llm_provider:
            case LLMProvider.ANTHROPIC:
                if not settings.anthropic_api_key:
                    raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
                logger.info("Initializing Anthropic model: %s", model)
                return ChatAnthropic(
                    model=model,
                    api_key=SecretStr(settings.anthropic_api_key),
                    timeout=30,
                )

            case LLMProvider.OPENAI:
                if not settings.openai_api_key:
                    raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
                logger.info("Initializing OpenAI model: %s", model)
                return ChatOpenAI(
                    model=model,
                    api_key=SecretStr(settings.openai_api_key),
                    timeout=30,
                )

            case LLMProvider.GEMINI:
                if not settings.google_api_key:
                    raise ValueError("GOOGLE_API_KEY is required for Gemini provider")
                logger.info("Initializing Gemini model: %s", model)
                return ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=SecretStr(settings.google_api_key),
                    timeout=30,
                )

            case LLMProvider.OPENROUTER:
                if not settings.openrouter_api_key:
                    raise ValueError("OPENROUTER_API_KEY is required for OpenRouter provider")
                logger.info("Initializing OpenRouter model: %s", model)
                return ChatOpenAI(
                    model=model,
                    api_key=SecretStr(settings.openrouter_api_key),
                    base_url="https://openrouter.ai/api/v1",
                    timeout=30,
                )

            case LLMProvider.Z_AI:
                if not settings.z_ai_api_key:
                    raise ValueError("Z_AI_API_KEY is required for Z-AI provider")
                logger.info("Initializing Z-AI model: %s", model)
                return ChatOpenAI(
                    model=model,
                    temperature=0.6,
                    openai_api_key=SecretStr(settings.z_ai_api_key),
                    openai_api_base="https://api.z.ai/api/anthropic",
                )

            case _:
                raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    except Exception as e:
        logger.error("Failed to initialize LLM: %s", str(e))
        raise


async def call_llm_with_retry(llm: BaseChatModel, messages: list) -> str:
    """Call LLM with retry logic and error handling.

    Args:
        llm: LLM instance
        messages: List of messages to send

    Returns:
        LLM response content

    Raises:
        LLMError: If all retry attempts fail
    """
    try:
        return await _retry_llm_call(llm, messages)
    except RetryError as e:
        logger.error("All LLM retry attempts failed: %s", str(e))
        raise LLMError(f"LLM operation failed after retries: {e!s}") from e
    except Exception as e:
        logger.error("Unexpected LLM error: %s", str(e))
        raise LLMError(f"LLM operation failed: {e!s}") from e
