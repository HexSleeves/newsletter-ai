"""Article summarization service using LLM via LangChain."""

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import call_llm_with_retry, get_llm
from app.logging_config import get_logger
from app.models import Article
from app.prompts import format_prompt, get_prompt, truncate_content


class SummarizationError(Exception):
    """Raised when article summarization fails after all retry attempts."""


logger = get_logger(__name__)


class ArticleSummarizer:
    """Summarizes articles using configured LLM provider."""

    def __init__(
        self,
        db_session,
        summary_style: Literal[
            "concise", "ultra_concise", "bullet_points", "structured"
        ] = "concise",
        max_content_chars: int = 1500,
    ):
        """Initialize article summarizer.

        Args:
            db_session: Database session
            summary_style: Type of summary to generate (default: concise)
            max_content_chars: Max chars to send to LLM (default: 1500, ~375 tokens)
        """
        self.db = db_session
        self.llm = get_llm()
        self.summary_style = summary_style
        self.max_content_chars = max_content_chars

    async def summarize_article(self, article: Article) -> str:
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

            summary = call_llm_with_retry(self.llm, messages)
            logger.info("Successfully generated summary for article %s", article.id)

            # Save to database with error handling
            try:
                article.summary = summary
                await self.db.commit()
                logger.debug("Saved summary for article %s", article.id)
            except Exception as e:
                logger.error("Database error saving summary for article %s: %s", article.id, str(e))
                await self.db.rollback()
                raise

            return summary

        except Exception as e:
            logger.error("Failed to summarize article %s: %s", article.id, str(e))
            raise

    async def summarize_articles(
        self, articles: list[Article], use_batch: bool = False
    ) -> list[Article]:
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
                return await self._batch_summarize(articles)

            # Process individually with error handling
            successful_count = 0
            failed_count = 0

            for article in articles:
                if not article.summary:
                    try:
                        await self.summarize_article(article)
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

    async def _batch_summarize(self, articles: list[Article], batch_size: int = 5) -> list[Article]:
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

                summary = call_llm_with_retry(self.llm, messages)
                logger.info("Successfully generated batch summary for articles %s", batch_ids)

                # Parse response and assign summaries
                summaries = self._parse_batch_response(summary.content, len(batch))

                for article, summary in zip(batch, summaries, strict=False):
                    article.summary = summary
                    await self.db.add(article)

                # Commit batch to database
                await self.db.commit()
                logger.info("Successfully saved batch summaries for articles %s", batch_ids)

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

        # Ensure we have right count
        while len(summaries) < expected_count:
            summaries.append("Summary unavailable")

        return summaries[:expected_count]
