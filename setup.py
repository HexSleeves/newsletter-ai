#!/usr/bin/env python3
"""Setup script for newsletter_backend."""

from setuptools import find_packages, setup

setup(
    name="newsletter_backend",
    version="0.1.0",
    packages=find_packages(exclude=["config*", "tests*"]),
    install_requires=[
        "aiohttp>=3.13.2",
        "fastapi>=0.122.0",
        "uvicorn[standard]>=0.38.0",
        "sqlalchemy>=2.0.44",
        "feedparser>=6.0.12",
        "anthropic>=0.75.0",
        "jinja2>=3.1.6",
        "python-dotenv>=1.2.1",
        "pydantic-settings>=2.12.0",
        "pydantic[email]>=2.12.5",
        "httpx>=0.28.1",
        "langchain>=1.1.0",
        "langchain-anthropic>=1.2.0",
        "langchain-openai>=1.1.0",
        "langchain-google-genai>=3.2.0",
        "resend>=2.19.0",
    ],
    python_requires=">=3.12",
)
