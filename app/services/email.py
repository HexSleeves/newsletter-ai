"""Email service for sending newsletters."""

from typing import Any

import resend

from app.logging_config import get_logger
from app.models import Newsletter, Subscriber
from config import settings

logger = get_logger(__name__)


class EmailService:
    """Service for sending newsletters via Resend."""

    def __init__(self):
        """Initialize email service with Resend API key."""
        resend.api_key = settings.resend_api_key

    def send_newsletter(
        self,
        subscriber: Subscriber,
        newsletter: Newsletter,
        from_email: str = "onboarding@resend.dev",
    ) -> bool:
        """Send a newsletter to a subscriber.

        Args:
            subscriber: Subscriber to send to
            newsletter: Newsletter to send
            from_email: Sender email address

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            params: resend.Emails.SendParams = {
                "from": from_email,
                "to": [subscriber.email],
                "subject": newsletter.title,
                "html": newsletter.html_content,
            }

            email: Any = resend.Emails.send(params)
            logger.info(
                "Sent newsletter %s to %s: %s", newsletter.id, subscriber.email, email["id"]
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to send newsletter %s to %s: %s", newsletter.id, subscriber.email, e
            )
            return False

    def send_to_all_subscribers(self, newsletter: Newsletter, db_session) -> dict[str, int]:
        """Send newsletter to all active subscribers.

        Args:
            newsletter: Newsletter to send
            db_session: Database session to query subscribers

        Returns:
            Dictionary with success and failure counts
        """
        subscribers = db_session.query(Subscriber).filter(Subscriber.is_active).all()

        logger.info("Sending newsletter %s to %s subscribers", newsletter.id, len(subscribers))

        params: list[resend.Emails.SendParams] = [
            {
                "from": "Test Newsletter <onboarding@resend.dev>",
                "to": [subscriber.email],
                "subject": newsletter.title,
                "html": newsletter.html_content,
            }
            for subscriber in subscribers
        ]

        try:
            resend.Batch.send(params)
            logger.info(
                "Successfully sent newsletter %s to %s subscribers", newsletter.id, len(subscribers)
            )

            return {"success": len(subscribers), "failure": 0}
        except Exception as e:
            logger.error("Failed to send newsletter %s: %s", newsletter.id, e)
            return {"success": 0, "failure": len(subscribers)}

        # for subscriber in subscribers:
        #     if self.send_newsletter(subscriber, newsletter):
        #         success_count += 1
        #     else:
        #         failure_count += 1

        # logger.info(
        #     "Finished sending newsletter %s: %s successes, %s failures",
        #     newsletter.id,
        #     success_count,
        #     failure_count,
        # )

        # return {"success": success_count, "failure": failure_count}
