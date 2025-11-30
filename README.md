# Newsletter AI Backend

A powerful FastAPI-based backend service for automating the creation and distribution of AI-curated newsletters. This system fetches articles from RSS feeds, summarizes them using various Large Language Models (LLMs), generates HTML newsletters, and distributes them via email.

## Features

- **Multi-Model LLM Support**: Seamlessly switch between OpenAI, Anthropic (Claude), Google Gemini, OpenRouter, and Z-AI for content generation.
- **Automated Content Aggregation**: Fetches and parses articles from configurable RSS feeds.
- **Intelligent Summarization**: Uses advanced LLMs to generate concise and engaging summaries of news articles.
- **Newsletter Generation**: Creates professionally formatted HTML newsletters using Jinja2 templates.
- **Email Distribution**: Integrated with Resend for reliable email delivery.
- **Admin API**: Protected endpoints for managing feeds, generating content, and sending emails.
- **SQLite Database**: Lightweight and efficient local data storage with SQLAlchemy.

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Database**: SQLAlchemy (SQLite)
- **LLM Integration**: [LangChain](https://www.langchain.com/)
- **Data Validation**: Pydantic v2
- **Task Management**: AsyncIO
- **Template Engine**: Jinja2
- **Email Service**: [Resend](https://resend.com/)
- **Package Management**: [uv](https://github.com/astral-sh/uv) (Recommended) or pip
- **Linting & Formatting**: Ruff

## Prerequisites

- Python 3.12 or higher
- `uv` package manager (recommended) or `pip`
- API Keys for:
  - Your chosen LLM Provider (OpenAI, Anthropic, Google, etc.)
  - Resend (for email sending)

## Installation

### Using uv (Recommended)

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd newsletter_backend
   ```

2. **Install dependencies:**

   ```bash
   make install
   # Or manually: uv sync
   ```

### Using pip

1. **Create a virtual environment:**

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install .
   ```

## Configuration

1. **Environment Setup:**
   Copy the example environment file and configure your secrets.

   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`:**
   Open `.env` and configure the following variables:

   **Core:**
   - `ADMIN_API_KEY`: Secret key for accessing admin endpoints (Required).
   - `DATABASE_URL`: Database connection string (Default: `sqlite:///./newsletter.db`).

   **LLM Configuration:**
   - `LLM_PROVIDER`: Choose from `openai`, `anthropic`, `gemini`, `openrouter`, `z_ai`.
   - `DEFAULT_MODEL`: Specific model name (e.g., `gpt-4-turbo`, `claude-3-opus`).
   - `OPENAI_API_KEY`: Required if using OpenAI.
   - `ANTHROPIC_API_KEY`: Required if using Anthropic.
   - `GOOGLE_API_KEY`: Required if using Gemini.
   - `OPENROUTER_API_KEY`: Required if using OpenRouter.

   **Email & Feeds:**
   - `RESEND_API_KEY`: API key from Resend.
   - `FROM_EMAIL`: Sender email address (e.g., `newsletter@yourdomain.com`).
   - `RSS_FEEDS`: Comma-separated list of RSS feed URLs.

## Running the Application

**Development Mode (with auto-reload):**

```bash
make dev
# Or manually: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode:**

```bash
make run
# Or manually: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
Access the interactive API docs at `http://localhost:8000/docs`.

## API Overview

### Public Endpoints

- `GET /api/articles`: List recent articles.
- `GET /api/articles/{id}`: Get a specific article.
- `GET /api/newsletter`: List recent newsletters.
- `GET /api/newsletter/{id}`: Get a specific newsletter.
- `POST /api/subscribe`: Subscribe to the newsletter.

### Admin Endpoints (Requires `X-Admin-Key` header)

- `POST /api/articles/fetch`: Trigger fetching and summarizing of new articles.
- `DELETE /api/articles/delete`: Delete old articles.
- `POST /api/newsletter/generate`: Generate a new newsletter from recent articles.
- `POST /api/newsletter/{id}/send`: Send a specific newsletter to subscribers.

## Development

**Run Tests:**

```bash
make test
```

**Linting:**

```bash
make lint
```

**Formatting:**

```bash
make format
```

## Project Structure

```bash
app/
├── api/            # API route handlers
├── services/       # Business logic (LLM, Fetcher, Generator, Email)
├── models.py       # SQLAlchemy database models
├── schemas.py      # Pydantic data models
├── llm.py          # LLM provider abstraction
├── templates/      # HTML templates for newsletters
└── main.py         # Application entry point
config.py           # Configuration management
```
