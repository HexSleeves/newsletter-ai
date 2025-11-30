"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field


class SubscribeRequest(BaseModel):
    """Request schema for subscribing an email."""

    email: EmailStr = Field(..., description="Email address to subscribe")


class UnsubscribeRequest(BaseModel):
    """Request schema for unsubscribing an email."""

    email: EmailStr = Field(..., description="Email address to unsubscribe")


class PaginationParams(BaseModel):
    """Pagination parameters for API endpoints."""

    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of items to return")
