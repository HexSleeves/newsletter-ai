# Newsletter AI Backend

Python FastAPI backend for fetching news articles, summarizing them with LLM, and generating newsletters.

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Run the server:**

```bash
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`

## API Endpoints

### Articles

- `POST /api/articles/fetch` - Fetch and summarize latest articles from RSS feeds
- `GET /api/articles` - List recent articles (default: 20)
- `GET /api/articles/{id}` - Get specific article

### Newsletters

- `POST /api/newsletter/generate?days=1` - Generate newsletter from recent articles
- `GET /api/newsletter` - List recent newsletters
- `GET /api/newsletter/{id}` - Get newsletter HTML

## Usage Example

```bash
# 1. Fetch articles from RSS feeds
curl -X POST http://localhost:8000/api/articles/fetch

# 2. Generate newsletter
curl -X POST http://localhost:8000/api/newsletter/generate?days=1

# 3. View newsletter
curl http://localhost:8000/api/newsletter/1
```

## Configuration

Edit `.env` to configure:

- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `RSS_FEEDS` - Comma-separated list of RSS feed URLs

## Tech Stack

- FastAPI - Web framework
- SQLAlchemy - ORM with SQLite
- feedparser - RSS feed parsing
- Anthropic Claude - Article summarization
- Jinja2 - Newsletter HTML templates
