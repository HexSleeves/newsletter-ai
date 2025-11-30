"""Database models for articles and newsletters."""

# pylint: disable=not-callable

from datetime import datetime, timedelta

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Article(Base):
    """News article from RSS feed."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(200), index=True)  # RSS feed source
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)  # Original content
    summary: Mapped[str] = mapped_column(Text, nullable=True)  # LLM-generated summary
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    newsletter_articles: Mapped[list["NewsletterArticle"]] = relationship(back_populates="article")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Article(id={self.id}, title='{self.title[:50]}...')>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Article: {self.title}"

    @property
    def has_summary(self) -> bool:
        """Check if the article has a summary."""
        return self.summary is not None and len(self.summary.strip()) > 0

    @property
    def is_recent(self) -> bool:
        """Check if the article was published recently (within last 7 days)."""

        return (datetime.now(self.published_at.tzinfo) - self.published_at) < timedelta(days=7)


class Newsletter(Base):
    """Generated newsletter."""

    __tablename__ = "newsletters"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    html_content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    newsletter_articles: Mapped[list["NewsletterArticle"]] = relationship(
        back_populates="newsletter"
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Newsletter(id={self.id}, title='{self.title}')>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Newsletter: {self.title}"

    @property
    def article_count(self) -> int:
        """Get the number of articles in this newsletter."""
        return len(self.newsletter_articles)


class NewsletterArticle(Base):
    """Association table between newsletters and articles."""

    __tablename__ = "newsletter_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    newsletter_id: Mapped[int] = mapped_column(ForeignKey("newsletters.id"))
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))

    # Relationships
    newsletter: Mapped["Newsletter"] = relationship(back_populates="newsletter_articles")
    article: Mapped["Article"] = relationship(back_populates="newsletter_articles")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"""<NewsletterArticle(id={self.id},
            newsletter_id={self.newsletter_id}, article_id={self.article_id})>"""

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"NewsletterArticle: newsletter {self.newsletter_id} -> article {self.article_id}"


class Subscriber(Base):
    """Newsletter subscriber."""

    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    subscribed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Subscriber(id={self.id}, email='{self.email}', active={self.is_active})>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "active" if self.is_active else "inactive"
        return f"Subscriber: {self.email} ({status})"

    def deactivate(self) -> None:
        """Deactivate the subscriber."""
        self.is_active = False

    def activate(self) -> None:
        """Activate the subscriber."""
        self.is_active = True
