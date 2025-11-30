"""Async newsletter generator service."""

from datetime import datetime, timedelta

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models import Article, Newsletter, NewsletterArticle


class NewsletterGenerator:
    """Generates HTML newsletters from articles."""

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
        try:
            self.env = Environment(loader=FileSystemLoader("app/templates"), enable_async=True)
        except Exception as e:
            self.logger.error("Failed to initialize template environment: %s", e)
            raise

    async def generate(self, days: int = 1) -> Newsletter:
        """Generate a newsletter from articles published in last N days."""
        try:
            self.logger.info("Generating newsletter for last %s days", days)

            # Get recent articles with summaries
            cutoff_date = datetime.now() - timedelta(days=days)
            try:
                articles = (
                    self.db.query(Article)
                    .filter(Article.published_at >= cutoff_date, Article.summary.isnot(None))
                    .order_by(Article.published_at.desc())
                    .all()
                )
            except SQLAlchemyError as e:
                self.logger.error("Database error fetching articles: %s", e)
                raise

            if not articles:
                self.logger.warning("No articles available for newsletter generation")
                raise ValueError("No articles available for newsletter generation")

            self.logger.info("Found %s articles for newsletter", len(articles))

            # Generate HTML from template
            try:
                template = self.env.get_template("newsletter.html")
                html_content = await template.render_async(
                    articles=articles,
                    date=datetime.now().strftime("%B %d, %Y"),
                    title=f"Daily Newsletter - {datetime.now().strftime('%Y-%m-%d')}",
                )
            except TemplateNotFound as e:
                self.logger.error("Template not found: %s", e)
                raise
            except Exception as e:
                self.logger.error("Template rendering error: %s", e)
                raise

            # Create newsletter record
            newsletter = Newsletter(
                title=f"Daily Newsletter - {datetime.now().strftime('%Y-%m-%d')}",
                html_content=html_content,
            )

            # Save to database with error handling
            try:
                self.db.add(newsletter)
                self.db.flush()  # Get newsletter ID

                # Associate articles with newsletter
                for article in articles:
                    assoc = NewsletterArticle(newsletter_id=newsletter.id, article_id=article.id)
                    self.db.add(assoc)

                self.db.commit()
                self.logger.info("Successfully generated newsletter %s", newsletter.id)
                return newsletter
            except SQLAlchemyError as e:
                self.logger.error("Database error saving newsletter: %s", e)
                self.db.rollback()
                raise

        except Exception as e:
            self.logger.error("Unexpected error generating newsletter: %s", str(e))
            raise

    async def get_newsletter(self, newsletter_id: int) -> Newsletter:
        """Get a newsletter by ID."""
        try:
            newsletter = self.db.query(Newsletter).filter_by(id=newsletter_id).first()
            if not newsletter:
                self.logger.warning("Newsletter %s not found", newsletter_id)
                raise ValueError(f"Newsletter {newsletter_id} not found")
            return newsletter
        except SQLAlchemyError as e:
            self.logger.error("Database error fetching newsletter %s: %s", newsletter_id, str(e))
            raise

    async def list_newsletters(self, limit: int = 10) -> list[Newsletter]:
        """List recent newsletters."""
        try:
            newsletters = (
                self.db.query(Newsletter).order_by(Newsletter.created_at.desc()).limit(limit).all()
            )
            self.logger.info("Retrieved %s newsletters", len(newsletters))
            return newsletters
        except SQLAlchemyError as e:
            self.logger.error("Database error listing newsletters: %s", str(e))
            raise
