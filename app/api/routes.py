"""API routes for the newsletter backend."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import verify_admin
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


# Article endpoints
@router.post("/articles/fetch", response_model=FetchResponse)
def fetch_articles(
    summary_style: str = "concise",
    use_batch: bool = False,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Fetch latest articles from RSS feeds and summarize them.

    Args:
        summary_style: Style of summary (concise, ultra_concise, bullet_points, structured)
        use_batch: Process summaries in batches for efficiency (trades quality for speed)
        db: Database session
    """
    try:
        logger.info(
            "Starting article fetch with summary_style=%s, use_batch=%s", summary_style, use_batch
        )

        fetcher = ArticleFetcher(db)
        summarizer = ArticleSummarizer(db, summary_style=summary_style)

        # Fetch articles
        articles = fetcher.fetch_all()
        logger.info("Fetched %s articles", len(articles))

        # Summarize new articles
        summarizer.summarize_articles(articles, use_batch=use_batch)
        logger.info("Summarized %s articles", len(articles))

        return {"articles_fetched": len(articles), "articles_summarized": len(articles)}

    except Exception as e:
        logger.error("Error in fetch_articles: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {str(e)}") from e


@router.get("/articles", response_model=list[ArticleResponse])
def list_articles(limit: int = 20, db: Session = Depends(get_db)):
    """List recent articles."""
    try:
        logger.info("Listing %s recent articles", limit)
        articles = db.query(Article).order_by(Article.published_at.desc()).limit(limit).all()
        logger.info("Retrieved %s articles", len(articles))
        return articles
    except SQLAlchemyError as e:
        logger.error("Database error listing articles: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve articles") from e
    except Exception as e:
        logger.error("Unexpected error listing articles: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/articles/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
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
def delete_articles(db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    """Delete all articles from the database."""
    try:
        logger.info("Deleting all articles from the database")
        db.query(Article).delete()
        db.commit()
        return {"articles_deleted": True}
    except Exception as e:
        logger.error("Error deleting articles: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete articles: {str(e)}") from e


# Newsletter endpoints
@router.post("/newsletter/generate", response_model=NewsletterResponse)
def generate_newsletter(
    days: int = 1, db: Session = Depends(get_db), _: None = Depends(verify_admin)
):
    """Generate a newsletter from recent articles."""
    try:
        logger.info("Generating newsletter for last %s days", days)
        generator = NewsletterGenerator(db)
        newsletter = generator.generate(days=days)
        logger.info("Successfully generated newsletter %s", newsletter.id)
        return newsletter
    except ValueError as e:
        logger.warning("Newsletter generation failed: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error generating newsletter: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to generate newsletter") from e


@router.get("/newsletter", response_model=list[NewsletterResponse])
def list_newsletters(limit: int = 10, db: Session = Depends(get_db)):
    """List recent newsletters."""
    try:
        logger.info("Listing %s recent newsletters", limit)
        generator = NewsletterGenerator(db)
        newsletters = generator.list_newsletters(limit=limit)
        return newsletters
    except SQLAlchemyError as e:
        logger.error("Database error listing newsletters: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve newsletters") from e
    except Exception as e:
        logger.error("Unexpected error listing newsletters: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/newsletter/{newsletter_id}", response_class=HTMLResponse)
def get_newsletter(newsletter_id: int, db: Session = Depends(get_db)):
    """Get a newsletter's HTML content."""
    try:
        logger.info("Retrieving newsletter %s", newsletter_id)
        generator = NewsletterGenerator(db)
        newsletter = generator.get_newsletter(newsletter_id)
        return newsletter.html_content
    except ValueError as e:
        logger.warning("Newsletter %s not found: %s", newsletter_id, str(e))
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error retrieving newsletter %s: %s", newsletter_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve newsletter") from e


@router.post("/newsletter/{newsletter_id}/send", response_model=SendNewsletterResponse)
def send_newsletter(
    newsletter_id: int, db: Session = Depends(get_db), _: None = Depends(verify_admin)
):
    """Send a newsletter to all active subscribers.

    Args:
        newsletter_id: ID of newsletter to send
        db: Database session
    """
    try:
        logger.info("Sending newsletter %s to all active subscribers", newsletter_id)

        # Get newsletter
        generator = NewsletterGenerator(db)
        newsletter = generator.get_newsletter(newsletter_id)

        # Send to all subscribers
        email_service = EmailService()
        results = email_service.send_to_all_subscribers(newsletter, db)

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


# Archive page
@router.get("/archive", response_class=HTMLResponse)
def newsletter_archive(request: Request, db: Session = Depends(get_db)):
    """Display newsletter archive page with subscription form.

    Args:
        request: FastAPI request object
        db: Database session
    """
    try:
        newsletters = db.query(Newsletter).order_by(Newsletter.created_at.desc()).limit(20).all()
        return templates.TemplateResponse(
            "archive.html",
            {"request": request, "newsletters": newsletters},
        )
    except Exception as e:
        logger.error("Error loading archive page: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to load archive") from e


# Subscriber endpoints
@router.post("/subscribe", response_model=SubscriberResponse)
def subscribe(email: str, db: Session = Depends(get_db)):
    """Subscribe an email address to the newsletter.

    Args:
        email: Email address to subscribe
        db: Database session
    """
    try:
        logger.info("Subscribing email: %s", email)

        # Check if already subscribed
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

        return {"status": "subscribed", "message": "Successfully subscribed to the newsletter!"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Database error subscribing %s: %s", email, str(e))
        raise HTTPException(status_code=500, detail="Failed to subscribe") from e
    except Exception as e:
        logger.error("Unexpected error subscribing %s: %s", email, str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/unsubscribe", response_model=SubscriberResponse)
def unsubscribe(email: str, db: Session = Depends(get_db)):
    """Unsubscribe an email address from the newsletter.

    Args:
        email: Email address to unsubscribe
        db: Database session
    """
    try:
        logger.info("Unsubscribing email: %s", email)

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
            "message": "Successfully unsubscribed from the newsletter",
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
