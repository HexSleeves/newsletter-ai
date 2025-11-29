"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database import init_db
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and logging on startup."""
    setup_logging()
    init_db()
    yield


app = FastAPI(
    title="Newsletter AI Backend",
    description=(
        "Backend service for fetching, summarizing, and generating newsletters from news articles"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "newsletter-ai-backend"}
