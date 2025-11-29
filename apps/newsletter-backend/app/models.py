"""Database models for articles and newsletters."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# pylint: disable=not-callable
class Article(Base):
    """News article from RSS feed."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000), unique=True)
    source: Mapped[str] = mapped_column(String(200))  # RSS feed source
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    content: Mapped[str] = mapped_column(Text, nullable=True)  # Original content
    summary: Mapped[str] = mapped_column(Text, nullable=True)  # LLM-generated summary
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )

    # Relationships
    newsletter_articles: Mapped[list["NewsletterArticle"]] = relationship(back_populates="article")


# pylint: disable=not-callable
class Newsletter(Base):
    """Generated newsletter."""

    __tablename__ = "newsletters"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    html_content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )

    # Relationships
    newsletter_articles: Mapped[list["NewsletterArticle"]] = relationship(
        back_populates="newsletter"
    )


class NewsletterArticle(Base):
    """Association table between newsletters and articles."""

    __tablename__ = "newsletter_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    newsletter_id: Mapped[int] = mapped_column(ForeignKey("newsletters.id"))
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))

    # Relationships
    newsletter: Mapped["Newsletter"] = relationship(back_populates="newsletter_articles")
    article: Mapped["Article"] = relationship(back_populates="newsletter_articles")
