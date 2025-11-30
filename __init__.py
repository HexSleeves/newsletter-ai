"""NewsletterBackend Backend Package"""

__version__ = "0.1.0"
__author__ = "NewsletterBackend"
__description__ = "NewsletterBackend Backend Package"
__url__ = "https://github.com/newsletterbackend/newsletter_backend"
__license__ = "MIT"
__copyright__ = "Copyright 2025 NewsletterBackend"
__maintainer__ = "NewsletterBackend"
__maintainer_email__ = "newsletterbackend@gmail.com"
__status__ = "Development"
__keywords__ = ["newsletter", "backend", "package"]
__classifiers__ = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
]


if __name__ == "__main__":
    import uvicorn

    # Import the FastAPI app from the app package
    from app.main import app

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")
