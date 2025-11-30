"""Simple API key authentication."""

from fastapi import Header, HTTPException

from config import settings


async def verify_admin(x_api_key: str = Header(...)):
    """Verify admin API key.

    Args:
        x_api_key: API key from request header

    Raises:
        HTTPException: If API key is invalid
    """
    if x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
