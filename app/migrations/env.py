"""Database migration for adding new indexes and updated_at timestamps."""

from sqlalchemy import text

from app.database import engine


def upgrade():
    """Add new indexes and updated_at timestamps."""
    # Add index to articles
    engine.execute(
        text("CREATE INDEX IF NOT EXISTS ix_articles_published_at ON articles (published_at)")
    )
    engine.execute(text("CREATE INDEX IF NOT EXISTS ix_articles_url ON articles (url)"))
    engine.execute(text("CREATE INDEX IF NOT EXISTS ix_articles_source ON articles (source)"))

    # Add updated_at to articles
    engine.execute(
        text("ALTER TABLE articles ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    )

    # Add updated_at to newsletters
    engine.execute(
        text("ALTER TABLE newsletters ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    )

    # Add index to newsletters.created_at
    engine.execute(
        text("CREATE INDEX IF NOT EXISTS ix_newsletters_created_at ON newsletters (created_at)")
    )


def downgrade():
    """Remove new indexes and updated_at timestamps."""
    # Drop new indexes
    engine.execute(text("DROP INDEX IF EXISTS ix_articles_published_at"))
    engine.execute(text("DROP INDEX IF EXISTS ix_articles_url"))
    engine.execute(text("DROP INDEX IF EXISTS ix_articles_source"))
    engine.execute(text("DROP INDEX IF EXISTS ix_newsletters_created_at"))

    # Drop updated_at columns
    engine.execute(text("ALTER TABLE articles DROP COLUMN updated_at"))
    engine.execute(text("ALTER TABLE newsletters DROP COLUMN updated_at"))
