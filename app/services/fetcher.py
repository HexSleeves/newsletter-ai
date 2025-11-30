"""Service for fetching articles from RSS feeds."""

from datetime import datetime

import feedparser
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import Article
from config import get_settings


class ArticleFetcher:
    """Fetches and stores articles from RSS feeds."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.logger = get_logger(__name__)

    def fetch_all(self, refresh: bool = False) -> list[Article]:
        """Fetch articles from all configured RSS feeds."""
        articles = []
        for feed_url in self.settings.rss_feed_list:
            try:
                feed_articles = self.fetch_from_feed(feed_url, refresh)
                articles.extend(feed_articles)
                self.logger.info(
                    "Successfully fetched %s articles from %s", len(feed_articles), feed_url
                )
            except Exception as e:
                self.logger.error("Failed to fetch articles from %s: %s", feed_url, str(e))
                continue
        return articles

    def fetch_from_feed(self, feed_url: str, refresh: bool = False) -> list[Article]:
        """Fetch articles from a single RSS feed."""
        try:
            self.logger.info("Fetching articles from %s", feed_url)
            feed = feedparser.parse(feed_url)

            if feed.bozo and feed.bozo_exception:
                self.logger.warning(
                    "Feed parsing warning for %s: %s", feed_url, feed.bozo_exception
                )

            if not hasattr(feed, "entries") or not feed.entries:
                self.logger.warning("No entries found in feed %s", feed_url)
                return []

            articles = []
            for entry in feed.entries:
                try:
                    article = self._process_entry(entry, feed_url, feed, refresh)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.error("Error processing entry from %s: %s", feed_url, str(e))
                    continue

            self._commit_articles(articles)
            return articles

        except Exception as e:
            self.logger.error("Failed to parse feed %s: %s", feed_url, str(e))
            raise

    def _process_entry(self, entry, feed_url: str, feed, refresh: bool = False) -> Article | None:
        """Process a single feed entry into an Article."""
        if not hasattr(entry, "link") or not entry.link:
            self.logger.warning("Entry missing link, skipping")
            return None

        # Check if article already exists
        try:
            existing = self.db.query(Article).filter_by(url=entry.link).first()
            if existing and not refresh:
                self.logger.debug("Article already exists: %s", entry.link)
                return None
        except SQLAlchemyError as e:
            self.logger.error("Database error checking existing article: %s", str(e))
            return None

        if refresh:
            self.logger.debug("Refreshing article: %s", entry.link)

        # Parse published date
        published_at = datetime.now()
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                time_struct = entry.published_parsed
                if time_struct and len(time_struct) >= 6:
                    published_at = datetime(*time_struct[:6])
            except (ValueError, TypeError) as e:
                self.logger.warning("Invalid publish date for %s: %s", entry.link, str(e))

        # Extract content
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].value if entry.content[0].value else ""
        elif hasattr(entry, "summary"):
            content = entry.summary or ""

        # Get source title
        source_title = feed_url
        if hasattr(feed, "feed") and hasattr(feed.feed, "title") and feed.feed.title:
            source_title = feed.feed.title

        # Create new article
        try:
            article = Article(
                title=getattr(entry, "title", "Untitled"),
                url=entry.link,
                source=source_title,
                published_at=published_at,
                content=content,
            )
            return article
        except Exception as e:
            self.logger.error("Error creating article from %s: %s", entry.link, e)
            return None

    def _commit_articles(self, articles: list[Article]) -> None:
        """Commit articles to database with error handling."""
        if not articles:
            return

        try:
            for article in articles:
                self.db.add(article)
            self.db.commit()
            self.logger.info("Successfully committed %s articles to database", len(articles))
        except SQLAlchemyError as e:
            self.logger.error("Database error committing articles: %s", e)
            self.db.rollback()
            raise
