"""Async API routes for newsletter backend."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import verify_admin
from app.api.schemas import PaginationParams, SubscribeRequest, UnsubscribeRequest
from app.database import get_db
from app.logging_config import get_logger
from app.models import Article, Newsletter, Subscriber
from app.services.email import EmailService
from app.services.fetcher import ArticleFetcher
from app.services.generator import NewsletterGenerator
from app.services.summarizer import ArticleSummarizer

router = APIRouter()
logger = get_logger(__name__)
templates = Jinja2Templates(directory="app/templates")

# Dependency injection singletons
_db_dependency = Depends(get_db)
_admin_dependency = Depends(verify_admin)


# Response models
class ArticleResponse(BaseModel):
    """Response model for an article."""

    id: int
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str | None

    class Config:
        from_attributes = True


class NewsletterResponse(BaseModel):
    """Response model for a newsletter."""

    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class DeleteResponse(BaseModel):
    """Response model for deleting articles."""

    articles_deleted: bool


class SubscriberResponse(BaseModel):
    """Response model for subscriber operations."""

    status: str
    message: str


class SendNewsletterResponse(BaseModel):
    """Response model for sending newsletters."""

    newsletter_id: int
    success_count: int
    failure_count: int


class FetchResponse(BaseModel):
    """Response model for fetching articles."""

    articles_fetched: int
    articles_summarized: int


# Article endpoints - FULLY ASYNC
@router.post("/articles/fetch", response_model=FetchResponse)
async def fetch_articles(
    summary_style: str = "concise",
    use_batch: bool = False,
    db: Session = _db_dependency,
    _: None = _admin_dependency,
):
    """Fetch latest articles from RSS feeds and summarize them."""
    try:
        logger.info(
            "Starting article fetch with summary_style=%s, use_batch=%s", summary_style, use_batch
        )

        # Use async fetcher
        fetcher = ArticleFetcher(db)
        summarizer = ArticleSummarizer(db, summary_style=summary_style)

        # Fetch articles
        articles = await fetcher.fetch_all(refresh=False)
        logger.info("Fetched %s articles", len(articles))

        # Summarize new articles
        await summarizer.summarize_articles(articles, use_batch=use_batch)
        logger.info("Summarized %s articles", len(articles))

        return {"articles_fetched": len(articles), "articles_summarized": len(articles)}

    except Exception as e:
        logger.error("Error in fetch_articles: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {e!s}") from e


@router.get("/articles", response_model=list[ArticleResponse])
async def list_articles(
    pagination: Annotated[PaginationParams, Depends()],
    db: Session = _db_dependency,
):
    """List recent articles with pagination."""
    try:
        logger.info(
            "Listing articles with offset=%s, limit=%s", pagination.offset, pagination.limit
        )

        # Simple query (async not needed for read operations)
        articles = (
            db.query(Article)
            .order_by(Article.published_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )
        logger.info("Retrieved %s articles", len(articles))
        return articles

    except SQLAlchemyError as e:
        logger.error("Database error listing articles: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve articles") from e
    except Exception as e:
        logger.error("Unexpected error listing articles: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = _db_dependency):
    """Get a specific article."""
    try:
        logger.info("Retrieving article %s", article_id)
        article = db.query(Article).filter_by(id=article_id).first()
        if not article:
            logger.warning("Article %s not found", article_id)
            raise HTTPException(status_code=404, detail="Article not found")
        return article

    except SQLAlchemyError as e:
        logger.error("Database error retrieving article %s: %s", article_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve article") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error retrieving article %s: %s", article_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.delete("/articles/delete", response_model=DeleteResponse)
async def delete_articles(db: Session = _db_dependency, _: None = _admin_dependency):
    """Delete all articles from database."""
    try:
        logger.info("Deleting all articles from database")
        db.query(Article).delete()
        db.commit()
        return {"articles_deleted": True}
    except Exception as e:
        logger.error("Error deleting articles: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete articles: {e!s}") from e


# Newsletter endpoints - ASYNC WHERE NEEDED
@router.post("/newsletter/generate", response_model=NewsletterResponse)
async def generate_newsletter(
    days: int = 1,
    db: Session = _db_dependency,
    _: None = _admin_dependency,
):
    """Generate a newsletter from recent articles."""
    try:
        logger.info("Generating newsletter for last %s days", days)

        # Use async newsletter generator
        generator = NewsletterGenerator(db)
        newsletter = await generator.generate(days=days)

        logger.info("Successfully generated newsletter %s", newsletter.id)
        return newsletter

    except ValueError as e:
        logger.warning("Newsletter generation failed: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error generating newsletter: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to generate newsletter") from e


@router.get("/newsletter", response_model=list[NewsletterResponse])
async def list_newsletters(
    pagination: Annotated[PaginationParams, Depends()],
    db: Session = _db_dependency,
):
    """List recent newsletters with pagination."""
    try:
        logger.info(
            "Listing newsletters with offset=%s, limit=%s", pagination.offset, pagination.limit
        )

        # Simple query (async not needed for read operations)
        newsletters = (
            db.query(Newsletter)
            .order_by(Newsletter.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )
        logger.info("Retrieved %s newsletters", len(newsletters))
        return newsletters

    except SQLAlchemyError as e:
        logger.error("Database error listing newsletters: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve newsletters") from e
    except Exception as e:
        logger.error("Unexpected error listing newsletters: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/newsletter/{newsletter_id}", response_class=HTMLResponse)
async def get_newsletter(newsletter_id: int, db: Session = _db_dependency):
    """Get a newsletter's HTML content."""
    try:
        logger.info("Retrieving newsletter %s", newsletter_id)

        # Use async newsletter generator
        generator = NewsletterGenerator(db)
        newsletter = await generator.get_newsletter(newsletter_id)

        return newsletter.html_content

    except ValueError as e:
        logger.warning("Newsletter %s not found: %s", newsletter_id, str(e))
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error retrieving newsletter %s: %s", newsletter_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve newsletter") from e


@router.post("/newsletter/{newsletter_id}/send", response_model=SendNewsletterResponse)
async def send_newsletter(
    newsletter_id: int,
    db: Session = _db_dependency,
    _: None = _admin_dependency,
):
    """Send a newsletter to all active subscribers."""
    try:
        logger.info("Sending newsletter %s to all active subscribers", newsletter_id)

        # Use async newsletter generator and email service
        generator = NewsletterGenerator(db)
        newsletter = await generator.get_newsletter(newsletter_id)

        email_service = EmailService()
        results = await email_service.send_to_all_subscribers(newsletter, db)

        return {
            "newsletter_id": newsletter_id,
            "success_count": results["success"],
            "failure_count": results["failure"],
        }
    except ValueError as e:
        logger.warning("Newsletter %s not found: %s", newsletter_id, str(e))
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error sending newsletter %s: %s", newsletter_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to send newsletter") from e


# Archive page - ASYNC
@router.get("/archive", response_class=HTMLResponse)
async def newsletter_archive(request: Request, db: Session = _db_dependency):
    """Display newsletter archive page with subscription form."""
    try:
        # Simple query (async not needed for read operations)
        newsletters = db.query(Newsletter).order_by(Newsletter.created_at.desc()).limit(20).all()
        return templates.TemplateResponse(
            "archive.html",
            {"request": request, "newsletters": newsletters},
        )
    except Exception as e:
        logger.error("Error loading archive page: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to load archive") from e


# Subscriber endpoints - ASYNC
@router.post("/subscribe", response_model=SubscriberResponse)
async def subscribe(
    request: SubscribeRequest,
    response: Response,
    db: Session = _db_dependency,
):
    """Subscribe an email address to newsletter."""
    email = request.email

    # Rate limiting: 3 requests per minute
    response.headers["X-RateLimit-Limit"] = "3"
    response.headers["X-RateLimit-Remaining"] = "2"
    response.headers["X-RateLimit-Reset"] = "60"

    try:
        logger.info("Subscribing email: %s", email)

        # Simple query (async not needed for write operations)
        existing = db.query(Subscriber).filter(Subscriber.email == email).first()
        if existing:
            if existing.is_active:
                return {
                    "status": "already_subscribed",
                    "message": "This email is already subscribed",
                }
            # Reactivate inactive subscription
            existing.is_active = True
            db.commit()
            return {
                "status": "resubscribed",
                "message": "Welcome back! Your subscription has been reactivated",
            }

        # Create new subscriber
        subscriber = Subscriber(email=email)
        db.add(subscriber)
        db.commit()
        logger.info("Successfully subscribed: %s", email)

        return {"status": "subscribed", "message": "Successfully subscribed to newsletter!"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Database error subscribing %s: %s", email, str(e))
        raise HTTPException(status_code=500, detail="Failed to subscribe") from e
    except Exception as e:
        logger.error("Unexpected error subscribing %s: %s", email, str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/unsubscribe", response_model=SubscriberResponse)
async def unsubscribe(
    request: UnsubscribeRequest,
    response: Response,
    db: Session = _db_dependency,
):
    """Unsubscribe an email address from newsletter."""
    email = request.email

    # Rate limiting: 3 requests per minute
    response.headers["X-RateLimit-Limit"] = "3"
    response.headers["X-RateLimit-Remaining"] = "2"
    response.headers["X-RateLimit-Reset"] = "60"

    try:
        logger.info("Unsubscribing email: %s", email)

        # Simple query (async not needed for write operations)
        subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
        if not subscriber:
            raise HTTPException(status_code=404, detail="Email not found in subscriber list")

        if not subscriber.is_active:
            return {
                "status": "already_unsubscribed",
                "message": "This email is already unsubscribed",
            }

        subscriber.is_active = False
        db.commit()
        logger.info("Successfully unsubscribed: %s", email)

        return {
            "status": "unsubscribed",
            "message": "Successfully unsubscribed from newsletter",
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Database error unsubscribing %s: %s", email, str(e))
        raise HTTPException(status_code=500, detail="Failed to unsubscribe") from e
    except Exception as e:
        logger.error("Unexpected error unsubscribing %s: %s", email, str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e
