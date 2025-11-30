"""Service for summarizing articles using LLM via LangChain."""

import time
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import Article
from app.prompts import format_prompt, get_prompt, truncate_content
from config import LLMProvider, get_settings


class SummarizationError(Exception):
    """Raised when article summarization fails after all retry attempts."""



logger = get_logger(__name__)


def get_llm() -> BaseChatModel:
    """Get the configured LLM instance."""
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
                    # max_tokens=200,
                    timeout=30,
                )

            case LLMProvider.OPENAI:
                if not settings.openai_api_key:
                    raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
                logger.info("Initializing OpenAI model: %s", model)
                return ChatOpenAI(
                    model=model,
                    api_key=SecretStr(settings.openai_api_key),
                    # max_tokens=200,
                    timeout=30,
                )

            case LLMProvider.GEMINI:
                if not settings.google_api_key:
                    raise ValueError("GOOGLE_API_KEY is required for Gemini provider")
                logger.info("Initializing Gemini model: %s", model)
                return ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=SecretStr(settings.google_api_key),
                    # max_output_tokens=200,
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
                    # max_tokens=200,
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
                    # openai_api_base="https://api.z.ai/api/paas/v4/",
                    openai_api_base="https://api.z.ai/api/anthropic",
                )

            case _:
                raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    except Exception as e:
        logger.error("Failed to initialize LLM: %s", str(e))
        raise


class ArticleSummarizer:
    """Summarizes articles using configured LLM provider."""

    def __init__(
        self,
        db: Session,
        summary_style: Literal[
            "concise", "ultra_concise", "bullet_points", "structured"
        ] = "concise",
        max_content_chars: int = 1500,
    ):
        """Initialize article summarizer.

        Args:
            db: Database session
            summary_style: Type of summary to generate (default: concise)
            max_content_chars: Max chars to send to LLM (default: 1500, ~375 tokens)
        """
        self.db = db
        self.llm = get_llm()
        self.summary_style = summary_style
        self.max_content_chars = max_content_chars

    def summarize_article(self, article: Article) -> str:
        """Generate a summary for a single article using optimized prompts.

        Args:
            article: Article to summarize

        Returns:
            Generated summary text
        """
        if not article.content:
            logger.warning("Article %s has no content, skipping summary", article.id)
            return "No content available for summary."

        try:
            logger.info("Summarizing article %s: %s", article.id, article.title[:50] + "...")

            # Get prompt template for configured style
            template = get_prompt("summary", self.summary_style)

            # Truncate content for token efficiency
            content = truncate_content(article.content, self.max_content_chars)

            # Format prompts
            system_msg, user_msg = format_prompt(template, title=article.title, content=content)

            # Invoke LLM with system + user messages with retry logic
            messages = [
                SystemMessage(content=system_msg),
                HumanMessage(content=user_msg),
            ]

            # Add retry logic for API failures
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.llm.invoke(messages)
                    summary = response.content.strip()

                    if not summary:
                        raise ValueError("Empty response from LLM")

                    logger.info("Successfully generated summary for article %s", article.id)

                    # Save to database with error handling
                    try:
                        article.summary = summary
                        self.db.commit()
                        logger.debug("Saved summary for article %s", article.id)
                    except SQLAlchemyError as e:
                        logger.error(
                            "Database error saving summary for article %s: %s", article.id, str(e)
                        )
                        self.db.rollback()
                        raise

                    return summary

                except Exception as e:
                    logger.warning(
                        "LLM attempt %d failed for article %s: %s", attempt + 1, article.id, str(e)
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)  # Exponential backoff
                    else:
                        raise SummarizationError(
                            f"Failed to summarize article {article.id} after {max_retries} "
                            f"attempts: {e!s}"
                        ) from e

        except Exception as e:
            logger.error("Error summarizing article %s: %s", article.id, str(e))
            # Return a fallback summary instead of failing completely
            fallback_summary = (
                f"Summary unavailable due to technical issues. Article: {article.title}"
            )
            try:
                article.summary = fallback_summary
                self.db.commit()
            except SQLAlchemyError:
                self.db.rollback()
            return fallback_summary

    def summarize_articles(self, articles: list[Article], use_batch: bool = False) -> list[Article]:
        """Summarize multiple articles.

        Args:
            articles: List of articles to summarize
            use_batch: If True, process in batches for efficiency (default: False)

        Returns:
            List of articles with summaries
        """
        try:
            logger.info(
                "Starting summarization of %d articles (use_batch=%s)", len(articles), use_batch
            )

            if use_batch:
                return self._batch_summarize(articles)

            # Process individually with error handling
            successful_count = 0
            failed_count = 0

            for article in articles:
                if not article.summary:
                    try:
                        self.summarize_article(article)
                        successful_count += 1
                    except Exception as e:
                        logger.error("Failed to summarize article %s: %s", article.id, str(e))
                        failed_count += 1
                        continue
                else:
                    successful_count += 1

            logger.info(
                "Summarization completed: %d successful, %d failed", successful_count, failed_count
            )
            return articles

        except Exception as e:
            logger.error("Unexpected error in summarize_articles: %s", str(e))
            raise

    def _batch_summarize(self, articles: list[Article], batch_size: int = 5) -> list[Article]:
        """Summarize articles in batches for token efficiency.

        Args:
            articles: List of articles to summarize
            batch_size: Number of articles per batch (default: 5)

        Returns:
            List of articles with summaries

        Note:
            Batch processing trades some quality for efficiency.
            Use for high-volume processing where speed matters.
        """
        from app.prompts import format_articles_batch

        unsummarized = [a for a in articles if not a.summary]
        logger.info("Batch summarizing %d articles in batches of %d", len(unsummarized), batch_size)

        for i in range(0, len(unsummarized), batch_size):
            batch = unsummarized[i : i + batch_size]
            batch_ids = [a.id for a in batch]

            try:
                logger.info("Processing batch %d-%d (articles: %s)", i, i + batch_size, batch_ids)

                # Format batch for processing
                article_data = [{"title": a.title, "content": a.content or ""} for a in batch]
                formatted_batch = format_articles_batch(article_data, max_articles=batch_size)

                # Get batch prompt
                template = get_prompt("batch", "bulk_summary")
                system_msg, user_msg = format_prompt(template, articles=formatted_batch)

                # Invoke LLM with retry logic
                messages = [
                    SystemMessage(content=system_msg),
                    HumanMessage(content=user_msg),
                ]

                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = self.llm.invoke(messages)

                        if not response or not response.content:
                            raise ValueError("Empty response from LLM")

                        logger.info(
                            "Successfully generated batch summary for articles %s", batch_ids
                        )
                        break

                    except Exception as e:  # Catch all exceptions during LLM calls for retry logic
                        logger.warning(
                            "Batch LLM attempt %d failed for articles %s: %s",
                            attempt + 1,
                            batch_ids,
                            str(e),
                        )
                        if attempt < max_retries - 1:
                            time.sleep(2**attempt)
                        else:
                            logger.error(
                                "Failed to summarize batch %s after %d attempts",
                                batch_ids,
                                max_retries,
                            )
                            # Use fallback summaries for this batch
                            for article in batch:
                                article.summary = (
                                    f"Batch summary unavailable due to technical issues. "
                                    f"Article: {article.title}"
                                )
                            continue

                # Parse response and assign summaries
                summaries = self._parse_batch_response(response.content, len(batch))

                for article, summary in zip(batch, summaries, strict=False):
                    article.summary = summary
                    self.db.add(article)

                # Commit batch to database
                try:
                    self.db.commit()
                    logger.info("Successfully saved batch summaries for articles %s", batch_ids)
                except SQLAlchemyError as e:
                    logger.error("Database error saving batch %s: %s", batch_ids, str(e))
                    self.db.rollback()
                    raise

            except Exception as e:
                logger.error("Error processing batch %s: %s", batch_ids, str(e))
                # Continue with next batch instead of failing completely
                continue

        return articles

    def _parse_batch_response(self, response: str, expected_count: int) -> list[str]:
        """Parse batch summarization response.

        Args:
            response: LLM response containing numbered summaries
            expected_count: Expected number of summaries

        Returns:
            List of individual summaries
        """
        summaries = []
        lines = response.strip().split("|")

        for line in lines:
            # Remove numbering like [1], [2], etc.
            clean = line.strip()
            if clean.startswith("[") and "]" in clean:
                clean = clean[clean.index("]") + 1 :].strip()
            if clean:
                summaries.append(clean)

        # Ensure we have the right count
        while len(summaries) < expected_count:
            summaries.append("Summary unavailable")

        return summaries[:expected_count]
