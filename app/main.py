"""Main FastAPI application."""

import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.database import init_db
from app.logging_config import setup_logging

# Suppress Pydantic V1 compatibility warning from langchain-core on Python 3.14+
# This is a known issue with langchain-core's internal compatibility shims
# and doesn't affect functionality since we're using Pydantic V2
# Must be set before any langchain imports
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="langchain_core._api.deprecation",
    message="Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.",
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize database and logging on startup."""
    setup_logging()
    init_db()
    yield


app = FastAPI(
    version="0.1.0",
    lifespan=lifespan,
    title="Newsletter AI Backend",
    description=(
        "Backend service for fetching, summarizing, and generating newsletters from news articles"
    ),
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router (async or sync based on availability)
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "newsletter-ai-backend"}
