# Newsletter Application Improvements

## Overview

Comprehensive improvements to transform the current newsletter application from a basic prototype into a production-ready system with frontend integration, automated workflows, robust error handling, and subscriber management.

**Current State:**

- ✅ FastAPI backend with RSS fetching and LLM summarization
- ✅ Multi-provider LLM support (Anthropic, OpenAI, Gemini)
- ✅ SQLAlchemy ORM with SQLite database
- ✅ Basic HTML newsletter generation via Jinja2
- ❌ No frontend UI (just Vite template)
- ❌ No automated scheduling
- ❌ No email delivery
- ❌ No tests
- ❌ No caching or rate limiting
- ❌ No authentication/authorization

## Problem Statement / Motivation

The application successfully fetches RSS feeds and generates LLM-powered summaries, but lacks critical features needed for production use:

1. **No User Experience:** The frontend is a placeholder template with no newsletter-specific UI
2. **Manual Operations:** All workflows require manual API calls (no automation)
3. **Missing Delivery:** Newsletters are generated but never sent to subscribers
4. **No Resilience:** Limited error handling, no caching, fragile batch processing
5. **Security Gaps:** Open CORS policy, no authentication, vulnerable to abuse
6. **Zero Tests:** Cannot refactor safely or deploy with confidence
7. **Scalability Issues:** No async operations, unbounded database growth, no pagination

**Why This Matters:**

- Cannot deploy to real users without email delivery and subscriber management
- Manual workflows don't scale beyond personal use
- Lack of tests and caching makes maintenance risky and costly
- Security vulnerabilities expose expensive LLM APIs to abuse

## Proposed Solution

### High-Level Approach

Transform the application into a production-ready newsletter service through phased improvements:

**Phase 1: Core Infrastructure** (Weeks 1-2)

- Async/await throughout the backend (FastAPI + SQLAlchemy async)
- Redis caching layer for RSS feeds and LLM responses
- Authentication and authorization (JWT tokens)
- Comprehensive pytest test suite

**Phase 2: Email & Scheduling** (Weeks 2-3)

- Email delivery integration (SendGrid/AWS SES)
- Subscriber management (database schema + API endpoints)
- Background task processing (Celery/ARQ)
- Automated scheduling (cron/EventBridge)

**Phase 3: Frontend Development** (Weeks 3-5)

- React-based web application for newsletter browsing
- Admin dashboard for feed management and analytics
- Subscriber portal for preferences and history
- Newsletter preview and testing UI

**Phase 4: Observability & Polish** (Weeks 5-6)

- Metrics collection and monitoring
- Cost tracking for LLM API usage
- Enhanced error handling with alerting
- Performance optimization and load testing

## Technical Considerations

### Architecture Impacts

**Migration to Async/Await:**

```python
# Current: Synchronous SQLAlchemy
with Session() as session:
    articles = session.query(Article).all()

# Proposed: Async SQLAlchemy
async with async_session() as session:
    result = await session.scalars(select(Article))
    articles = result.all()
```

**Benefits:**

- 5-10x faster RSS fetching with concurrent requests
- Non-blocking LLM API calls
- Better resource utilization
- Native FastAPI async support

**Tradeoffs:**

- Requires rewriting database layer
- More complex error handling
- Requires async-compatible libraries

**Affected Files:**

- `/Users/jacob.lecoq.ext/Projects/ai_projects/newsletter-ai/apps/newsletter-backend/app/database.py`
- `/Users/jacob.lecoq.ext/Projects/ai_projects/newsletter-ai/apps/newsletter-backend/app/api/routes.py`
- `/Users/jacob.lecoq.ext/Projects/ai_projects/newsletter-ai/apps/newsletter-backend/app/services/fetcher.py`

### Performance Implications

**Caching Strategy:**

| Resource | Cache Type | TTL | Impact |
|----------|-----------|-----|--------|
| RSS Feeds | Cache-Aside | 1 hour | Reduces feed provider requests by 95%+ |
| LLM Summaries | Write-Through | Indefinite | Saves $0.01-0.10 per duplicate article |
| Article Queries | Read-Through | 5 minutes | Reduces DB load by 60-80% |

**Implementation:**

```python
import redis.asyncio as redis
from functools import wraps

async def get_redis():
    return await redis.from_url("redis://localhost:6379")

async def cached_feed(url: str) -> str:
    r = await get_redis()
    cached = await r.get(f"feed:{url}")
    if cached:
        return cached.decode()

    content = await fetch_feed(url)  # Actual HTTP request
    await r.setex(f"feed:{url}", 3600, content)  # 1 hour TTL
    return content
```

**Expected Performance:**

- Fetch time: 10s → 2s (5 feeds fetched concurrently)
- LLM cost reduction: 30-50% (deduplication via caching)
- API response time: 500ms → 50ms (cached queries)

### Security Considerations

**Authentication System:**

- JWT tokens with 24-hour expiration
- Role-based access control (Admin, Subscriber, Guest)
- API key authentication for programmatic access
- Rate limiting: 10 req/min for guests, 100 req/min for authenticated users

**Endpoint Protection:**

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_admin(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload

@app.post("/api/articles/fetch")
async def fetch_articles(admin: dict = Depends(verify_admin)):
    # Only admins can trigger expensive LLM operations
    ...
```

**CORS Update:**

```python
# Current (apps/newsletter-backend/app/main.py:33)
allow_origins=["*"]  # ❌ Accepts requests from anywhere

# Proposed
allow_origins=[
    "https://newsletter.example.com",
    "http://localhost:5173",  # Vite dev server
]
```

**Secrets Management:**

- Migrate from `.env` files to AWS Secrets Manager or HashiCorp Vault
- Use `pydantic.SecretStr` for sensitive values (already implemented in summarizer.py)
- Rotate API keys quarterly

## Acceptance Criteria

### Functional Requirements

**Must Have (MVP):**

- [ ] Async/await implemented across all backend services
- [ ] Redis caching for RSS feeds (1-hour TTL) and LLM summaries (indefinite)
- [ ] JWT authentication protecting admin endpoints
- [ ] Email delivery via SendGrid/AWS SES with subscriber management
- [ ] Subscriber database schema (users, subscriptions, preferences)
- [ ] Background task processing for fetch/summarize/generate/send pipeline
- [ ] Scheduled daily newsletter generation (cron/EventBridge)
- [ ] React frontend displaying newsletter archive and article browsing
- [ ] Admin dashboard for managing RSS feeds and viewing stats
- [ ] Subscriber portal for managing preferences (frequency, topics)
- [ ] Pytest suite with 80%+ coverage (unit + integration tests)
- [ ] Rate limiting on all public endpoints (10 req/min)

**Should Have:**

- [ ] Newsletter preview UI before sending
- [ ] A/B testing framework for different summary styles
- [ ] Metrics collection (Prometheus/CloudWatch)
- [ ] Cost tracking for LLM API usage per newsletter
- [ ] Retry queue for failed summarizations (dead letter queue)
- [ ] Circuit breaker for failing RSS feeds
- [ ] Database indexes for common queries
- [ ] Migration to PostgreSQL from SQLite
- [ ] Comprehensive error handling with Sentry integration
- [ ] Newsletter open/click tracking

**Nice to Have:**

- [ ] Multi-language support
- [ ] Content moderation workflow
- [ ] Mobile app (iOS/Android)
- [ ] Export newsletters to PDF/Markdown
- [ ] Personalized newsletters based on user interests
- [ ] Newsletter template customization UI
- [ ] Advanced analytics dashboard

### Non-Functional Requirements

**Performance:**

- [ ] Newsletter generation completes in < 30 seconds (10 articles, concurrent summarization)
- [ ] API responses return in < 200ms (95th percentile, cached)
- [ ] Support 10,000 subscribers without degradation
- [ ] Handle 50+ concurrent RSS feed fetches

**Security:**

- [ ] All endpoints require authentication except public archive
- [ ] Rate limiting prevents abuse of LLM APIs
- [ ] CORS restricted to known frontends
- [ ] API keys stored in secrets manager (not .env files)
- [ ] Input validation on all user-provided data
- [ ] XSS protection for HTML content from RSS feeds

**Reliability:**

- [ ] 99.9% uptime for newsletter delivery
- [ ] Graceful degradation when LLM provider is unavailable (fallback summaries)
- [ ] Automatic retry with exponential backoff for transient failures
- [ ] Dead letter queue for items that fail after 3 retries
- [ ] Alerting via Slack/PagerDuty for critical failures

**Maintainability:**

- [ ] 80%+ test coverage across all modules
- [ ] API documentation via FastAPI automatic docs
- [ ] Architecture decision records (ADR) for major changes
- [ ] Deployment documentation and runbooks
- [ ] Monitoring dashboards for system health

## Success Metrics

**Operational Metrics:**

- Daily active subscribers > 100 within first month
- Newsletter delivery success rate > 99.5%
- LLM API cost < $0.50 per newsletter (50 articles)
- Average newsletter generation time < 30 seconds
- Zero security incidents or abuse

**Quality Metrics:**

- Test coverage > 80% across all modules
- Zero critical bugs in production after 1 week
- P95 API response time < 200ms
- RSS feed fetch success rate > 95%

**User Engagement Metrics:**

- Newsletter open rate > 25%
- Click-through rate > 5%
- Unsubscribe rate < 2%
- Average session duration on archive > 3 minutes

## Dependencies & Risks

### Dependencies

**External Services:**

- SendGrid or AWS SES for email delivery (requires account setup, domain verification)
- Redis for caching (can use managed service like AWS ElastiCache or self-hosted)
- PostgreSQL for database (migration from SQLite required)
- LLM API providers (Anthropic, OpenAI, Gemini) - already configured

**Infrastructure:**

- Celery/ARQ requires message broker (Redis or RabbitMQ)
- Scheduled tasks require cron or AWS EventBridge
- Production deployment requires hosting (AWS, GCP, or similar)

**Frontend Dependencies:**

- React migration (current Vite template is vanilla TypeScript)
- Component library decision (shadcn/ui, Material-UI, or custom)
- State management (React Query, Zustand, or Context API)

### Prerequisites

1. **Environment Setup:**
   - Redis instance running locally or accessible remotely
   - PostgreSQL database provisioned
   - Email provider account configured (SendGrid API key or AWS SES credentials)

2. **Design Decisions:**
   - Choose email provider (SendGrid vs. AWS SES vs. Resend)
   - Choose background task system (Celery vs. ARQ vs. FastAPI BackgroundTasks)
   - Choose frontend state management approach
   - Define subscriber schema and preferences model

3. **Domain/DNS:**
   - Domain for email sending (SPF, DKIM, DMARC records)
   - SSL certificate for production deployment

### Risk Analysis & Mitigation

**High Risk:**

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **LLM API Cost Explosion** | $1000s in unexpected charges | Medium | Implement per-user rate limits, caching, cost monitoring with alerts |
| **Email Deliverability Issues** | Newsletters land in spam, low open rates | High | Proper SPF/DKIM/DMARC setup, warm up IP, monitor bounce/spam rates |
| **Database Migration Failures** | Data loss during SQLite → PostgreSQL migration | Low | Full backup before migration, staged rollout, rollback plan |
| **Security Breach** | LLM API keys leaked, unauthorized access | Medium | Secrets manager, JWT expiration, audit logging, penetration testing |

**Medium Risk:**

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **RSS Feed Changes** | Parsing breaks when feed structure changes | Medium | Schema validation, fallback parsers, alerting on parse failures |
| **Performance Degradation** | Slow responses under load | Medium | Load testing, caching, async operations, database indexes |
| **Batch Summarization Parsing Errors** | Incorrect article-summary mappings | High | Replace pipe-delimited parsing with JSON structured output |
| **Incomplete Test Coverage** | Bugs slip into production | Medium | Enforce coverage thresholds in CI/CD, prioritize critical paths |

**Low Risk:**

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **Frontend Framework Churn** | React patterns change, dependencies outdated | Low | Lock major versions, gradual upgrades, comprehensive E2E tests |
| **Celery/ARQ Complexity** | Background tasks harder to debug | Low | Thorough logging, task monitoring dashboard, retries with DLQ |

## Technical Approach

### Phase 1: Async Migration & Caching (Week 1)

**Goals:**

- Convert backend to fully async
- Implement Redis caching
- Add basic authentication

**Tasks:**

1. **Async SQLAlchemy Migration** (`apps/newsletter-backend/app/database.py`)

   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

   engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/newsletter")
   async_session = async_sessionmaker(engine, expire_on_commit=False)
   ```

2. **Async Route Handlers** (`apps/newsletter-backend/app/api/routes.py`)

   ```python
   @app.get("/api/articles")
   async def get_articles(
       limit: int = 20,
       db: AsyncSession = Depends(get_async_db)
   ):
       result = await db.scalars(
           select(Article)
           .order_by(Article.published_date.desc())
           .limit(limit)
       )
       return result.all()
   ```

3. **Async RSS Fetching** (`apps/newsletter-backend/app/services/fetcher.py`)

   ```python
   import httpx
   import asyncio

   async def fetch_all_feeds(feed_urls: list[str]) -> list[dict]:
       async with httpx.AsyncClient(timeout=30.0) as client:
           tasks = [fetch_single_feed(client, url) for url in feed_urls]
           return await asyncio.gather(*tasks, return_exceptions=True)
   ```

4. **Redis Caching Layer** (`apps/newsletter-backend/app/services/cache.py`)

   ```python
   import redis.asyncio as redis
   from typing import Optional

   class CacheService:
       def __init__(self, redis_url: str = "redis://localhost:6379"):
           self.redis = redis.from_url(redis_url)

       async def get_feed(self, url: str) -> Optional[str]:
           return await self.redis.get(f"feed:{url}")

       async def set_feed(self, url: str, content: str, ttl: int = 3600):
           await self.redis.setex(f"feed:{url}", ttl, content)
   ```

5. **JWT Authentication** (`apps/newsletter-backend/app/auth.py`)

   ```python
   from fastapi import Depends, HTTPException, Security
   from fastapi.security import HTTPBearer
   import jwt

   security = HTTPBearer()

   async def get_current_user(
       credentials = Security(security)
   ) -> dict:
       try:
           payload = jwt.decode(
               credentials.credentials,
               settings.jwt_secret,
               algorithms=["HS256"]
           )
           return payload
       except jwt.InvalidTokenError:
           raise HTTPException(status_code=401, detail="Invalid token")
   ```

**Acceptance:**

- [ ] All routes are async
- [ ] RSS feeds fetched concurrently (5 feeds in ~2s vs. 10s sequential)
- [ ] Redis caching reduces duplicate feed fetches by 95%+
- [ ] JWT authentication protects admin endpoints

### Phase 2: Email & Subscribers (Week 2)

**Goals:**

- Subscriber management schema and API
- Email delivery integration
- Background task processing

**Tasks:**

1. **Database Schema** (`apps/newsletter-backend/app/models.py`)

   ```python
   class Subscriber(Base):
       __tablename__ = "subscribers"

       id = Column(Integer, primary_key=True)
       email = Column(String, unique=True, nullable=False, index=True)
       subscribed_at = Column(DateTime, default=datetime.utcnow)
       is_active = Column(Boolean, default=True)
       preferences = Column(JSON)  # {frequency: "daily", topics: [...]}

   class NewsletterDelivery(Base):
       __tablename__ = "newsletter_deliveries"

       id = Column(Integer, primary_key=True)
       newsletter_id = Column(Integer, ForeignKey("newsletters.id"))
       subscriber_id = Column(Integer, ForeignKey("subscribers.id"))
       sent_at = Column(DateTime)
       status = Column(Enum("pending", "sent", "failed", "bounced"))
       opened_at = Column(DateTime, nullable=True)
       clicked_at = Column(DateTime, nullable=True)
   ```

2. **Subscriber API Endpoints** (`apps/newsletter-backend/app/api/subscribers.py`)

   ```python
   @router.post("/api/subscribe")
   async def subscribe(email: str, db: AsyncSession = Depends(get_async_db)):
       subscriber = Subscriber(email=email)
       db.add(subscriber)
       await db.commit()
       # Send confirmation email
       return {"status": "subscribed"}

   @router.post("/api/unsubscribe/{token}")
   async def unsubscribe(token: str, db: AsyncSession = Depends(get_async_db)):
       # Verify token, deactivate subscriber
       ...
   ```

3. **Email Service** (`apps/newsletter-backend/app/services/email.py`)

   ```python
   from sendgrid import SendGridAPIClient
   from sendgrid.helpers.mail import Mail

   class EmailService:
       def __init__(self, api_key: str):
           self.client = SendGridAPIClient(api_key)

       async def send_newsletter(
           self,
           subscriber: Subscriber,
           newsletter: Newsletter
       ):
           message = Mail(
               from_email="newsletter@example.com",
               to_emails=subscriber.email,
               subject=f"Daily Newsletter - {newsletter.created_at.date()}",
               html_content=newsletter.content
           )

           try:
               response = self.client.send(message)
               return response.status_code == 202
           except Exception as e:
               logger.error(f"Failed to send to {subscriber.email}: {e}")
               return False
   ```

4. **Background Tasks** (`apps/newsletter-backend/app/tasks.py`)

   ```python
   from celery import Celery

   celery_app = Celery("newsletter", broker="redis://localhost:6379")

   @celery_app.task
   def send_newsletter_task(newsletter_id: int):
       # Fetch newsletter, loop through subscribers, send emails
       newsletter = get_newsletter(newsletter_id)
       subscribers = get_active_subscribers()

       for subscriber in subscribers:
           email_service.send_newsletter(subscriber, newsletter)
           # Track delivery status in NewsletterDelivery table
   ```

**Acceptance:**

- [ ] Subscribers can subscribe/unsubscribe via API
- [ ] Emails sent successfully via SendGrid/SES
- [ ] Background tasks process newsletter sending
- [ ] Delivery status tracked in database

### Phase 3: Scheduling & Automation (Week 2-3)

**Goals:**

- Automated daily newsletter generation
- Scheduled RSS fetching

**Tasks:**

1. **Celery Beat Scheduler** (`apps/newsletter-backend/celerybeat-schedule.py`)

   ```python
   from celery.schedules import crontab

   celery_app.conf.beat_schedule = {
       "fetch-rss-feeds-hourly": {
           "task": "tasks.fetch_and_summarize",
           "schedule": crontab(minute=0),  # Every hour
       },
       "generate-daily-newsletter": {
           "task": "tasks.generate_and_send_newsletter",
           "schedule": crontab(hour=8, minute=0),  # 8am daily
       },
   }
   ```

2. **Automated Pipeline Task** (`apps/newsletter-backend/app/tasks.py`)

   ```python
   @celery_app.task
   def generate_and_send_newsletter():
       # 1. Fetch articles from last 24 hours
       articles = get_recent_articles(days=1)

       # 2. Generate newsletter HTML
       newsletter = generate_newsletter(articles)

       # 3. Queue sending tasks for all subscribers
       send_newsletter_task.delay(newsletter.id)
   ```

**Acceptance:**

- [ ] RSS feeds fetched automatically every hour
- [ ] Daily newsletter generated and sent at 8am
- [ ] Failed tasks automatically retry with exponential backoff

### Phase 4: Frontend Development (Weeks 3-5)

**Goals:**

- React-based newsletter archive
- Admin dashboard
- Subscriber portal

**Tasks:**

1. **React Setup** (`apps/web/`)

   ```bash
   cd apps/web
   bun add react react-dom react-router-dom @tanstack/react-query
   bun add -d @types/react @types/react-dom
   ```

2. **Newsletter Archive Component** (`apps/web/src/components/NewsletterArchive.tsx`)

   ```tsx
   import { useQuery } from '@tanstack/react-query';

   function NewsletterArchive() {
     const { data: newsletters } = useQuery({
       queryKey: ['newsletters'],
       queryFn: () => fetch('/api/newsletter?limit=20').then(r => r.json())
     });

     return (
       <div className="newsletter-archive">
         {newsletters?.map(newsletter => (
           <NewsletterCard key={newsletter.id} newsletter={newsletter} />
         ))}
       </div>
     );
   }
   ```

3. **Admin Dashboard** (`apps/web/src/pages/AdminDashboard.tsx`)

   ```tsx
   function AdminDashboard() {
     return (
       <div className="admin-dashboard">
         <FeedManager />
         <NewsletterStats />
         <SubscriberList />
         <TriggerFetchButton />
       </div>
     );
   }
   ```

4. **API Integration** (`apps/web/src/lib/api.ts`)

   ```typescript
   const API_BASE = 'http://localhost:8000';

   export const api = {
     getNewsletters: () => fetch(`${API_BASE}/api/newsletter`).then(r => r.json()),
     getArticles: (limit = 20) => fetch(`${API_BASE}/api/articles?limit=${limit}`).then(r => r.json()),
     subscribe: (email: string) => fetch(`${API_BASE}/api/subscribe`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ email })
     }),
   };
   ```

**Acceptance:**

- [ ] Newsletter archive displays past newsletters with pagination
- [ ] Admin dashboard allows managing RSS feeds
- [ ] Subscriber portal shows subscription preferences
- [ ] Responsive design works on mobile and desktop

### Phase 5: Testing (Week 4)

**Goals:**

- 80%+ test coverage
- Unit tests for services
- Integration tests for API endpoints
- E2E tests for critical flows

**Tasks:**

1. **Test Setup** (`apps/newsletter-backend/tests/conftest.py`)

   ```python
   import pytest
   from httpx import AsyncClient
   from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

   @pytest.fixture
   async def test_db():
       engine = create_async_engine("sqlite+aiosqlite:///:memory:")
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)

       async_session = async_sessionmaker(engine, expire_on_commit=False)
       yield async_session

       await engine.dispose()

   @pytest.fixture
   async def client(test_db):
       app.dependency_overrides[get_async_db] = lambda: test_db()
       async with AsyncClient(app=app, base_url="http://test") as ac:
           yield ac
   ```

2. **Unit Tests** (`apps/newsletter-backend/tests/test_summarizer.py`)

   ```python
   @pytest.mark.asyncio
   async def test_summarize_article():
       summarizer = SummarizerService(provider="anthropic")

       article = Article(
           title="Test Article",
           content="This is a test article about technology.",
           url="https://example.com/test"
       )

       summary = await summarizer.summarize_article(article)

       assert len(summary) > 0
       assert len(summary) < 500  # Should be concise
   ```

3. **Integration Tests** (`apps/newsletter-backend/tests/test_api.py`)

   ```python
   @pytest.mark.asyncio
   async def test_fetch_articles_endpoint(client):
       response = await client.post("/api/articles/fetch")
       assert response.status_code == 200

       data = response.json()
       assert "articles_fetched" in data
       assert "summaries_generated" in data
   ```

4. **E2E Tests** (`apps/newsletter-backend/tests/test_e2e.py`)

   ```python
   @pytest.mark.asyncio
   async def test_full_newsletter_pipeline(client, test_db):
       # 1. Fetch articles
       await client.post("/api/articles/fetch")

       # 2. Generate newsletter
       response = await client.post("/api/newsletter/generate?days=1")
       newsletter_id = response.json()["id"]

       # 3. Verify newsletter content
       newsletter_response = await client.get(f"/api/newsletter/{newsletter_id}")
       assert newsletter_response.status_code == 200
       assert "html" in newsletter_response.text
   ```

**Acceptance:**

- [ ] 80%+ test coverage across all modules
- [ ] All critical paths have integration tests
- [ ] E2E tests verify complete workflows
- [ ] Tests run in CI/CD pipeline

### Phase 6: Observability & Monitoring (Week 5-6)

**Goals:**

- Metrics collection
- Cost tracking
- Error monitoring
- Performance dashboards

**Tasks:**

1. **Prometheus Metrics** (`apps/newsletter-backend/app/metrics.py`)

   ```python
   from prometheus_client import Counter, Histogram, Gauge

   articles_fetched = Counter("articles_fetched_total", "Total articles fetched")
   summaries_generated = Counter("summaries_generated_total", "Total summaries generated", ["provider"])
   llm_api_cost = Counter("llm_api_cost_total", "Total LLM API cost in USD", ["provider"])
   newsletter_generation_time = Histogram("newsletter_generation_seconds", "Newsletter generation time")
   active_subscribers = Gauge("active_subscribers", "Number of active subscribers")
   ```

2. **Cost Tracking** (`apps/newsletter-backend/app/services/summarizer.py`)

   ```python
   async def summarize_article(self, article: Article) -> str:
       start_time = time.time()

       response = await self.llm.ainvoke(messages)

       # Track cost based on token usage
       cost = self._calculate_cost(response.usage)
       llm_api_cost.labels(provider=self.provider).inc(cost)

       duration = time.time() - start_time
       summaries_generated.labels(provider=self.provider).inc()

       return response.content

   def _calculate_cost(self, usage: dict) -> float:
       # Pricing per 1M tokens (as of 2025)
       pricing = {
           "anthropic": {"input": 3.00, "output": 15.00},  # Claude Sonnet
           "openai": {"input": 2.50, "output": 10.00},    # GPT-4.1
           "google": {"input": 0.075, "output": 0.30},     # Gemini Flash
       }

       rates = pricing[self.provider]
       cost = (
           usage["input_tokens"] * rates["input"] / 1_000_000 +
           usage["output_tokens"] * rates["output"] / 1_000_000
       )
       return cost
   ```

3. **Error Monitoring** (`apps/newsletter-backend/app/main.py`)

   ```python
   import sentry_sdk
   from sentry_sdk.integrations.fastapi import FastApiIntegration

   sentry_sdk.init(
       dsn=settings.sentry_dsn,
       integrations=[FastApiIntegration()],
       traces_sample_rate=0.1,
   )
   ```

4. **Alerting** (`apps/newsletter-backend/app/alerts.py`)

   ```python
   async def check_newsletter_delivery_success_rate():
       success_rate = calculate_delivery_success_rate()

       if success_rate < 0.95:  # Below 95%
           await send_alert_to_slack(
               f"🚨 Newsletter delivery success rate dropped to {success_rate:.1%}"
           )
   ```

**Acceptance:**

- [ ] Prometheus metrics exported at `/metrics` endpoint
- [ ] LLM API costs tracked per newsletter and per provider
- [ ] Sentry captures and aggregates errors
- [ ] Slack alerts for critical failures

## Implementation Files

### New Files to Create

**Backend:**

```
apps/newsletter-backend/
├── app/
│   ├── auth.py                    # JWT authentication
│   ├── metrics.py                 # Prometheus metrics
│   ├── alerts.py                  # Alerting logic
│   ├── api/
│   │   ├── subscribers.py         # Subscriber management endpoints
│   │   └── admin.py               # Admin-only endpoints
│   ├── services/
│   │   ├── cache.py               # Redis caching service
│   │   └── email.py               # Email delivery service
│   └── tasks.py                   # Celery background tasks
├── tests/
│   ├── conftest.py                # Pytest fixtures
│   ├── test_summarizer.py        # Unit tests for summarizer
│   ├── test_fetcher.py            # Unit tests for fetcher
│   ├── test_api.py                # Integration tests for API
│   └── test_e2e.py                # End-to-end tests
└── celerybeat-schedule.py         # Celery Beat scheduler config
```

**Frontend:**

```
apps/web/
├── src/
│   ├── components/
│   │   ├── NewsletterArchive.tsx
│   │   ├── NewsletterCard.tsx
│   │   ├── ArticleList.tsx
│   │   └── SubscribeForm.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── AdminDashboard.tsx
│   │   └── SubscriberPortal.tsx
│   ├── lib/
│   │   ├── api.ts                 # API client
│   │   └── auth.ts                # Authentication helpers
│   └── App.tsx                    # Main app component
```

### Files to Modify

**Backend:**

- `apps/newsletter-backend/app/database.py` - Convert to async SQLAlchemy
- `apps/newsletter-backend/app/api/routes.py` - Convert routes to async, add auth
- `apps/newsletter-backend/app/services/fetcher.py` - Async RSS fetching with caching
- `apps/newsletter-backend/app/services/summarizer.py` - Add cost tracking, fix batch parsing
- `apps/newsletter-backend/app/models.py` - Add Subscriber, NewsletterDelivery models
- `apps/newsletter-backend/app/main.py` - Update CORS, add Sentry, add metrics endpoint
- `apps/newsletter-backend/config.py` - Add email provider config, Redis URL, JWT secret
- `apps/newsletter-backend/pyproject.toml` - Add dependencies (redis, celery, sendgrid, pytest-asyncio)

**Frontend:**

- `apps/web/src/main.ts` - Convert to React application
- `apps/web/package.json` - Add React dependencies
- `apps/web/vite.config.ts` - Add API proxy configuration

## References & Research

### Internal References

**Current Implementation:**

- Backend main app: `apps/newsletter-backend/app/main.py:1-47`
- API routes: `apps/newsletter-backend/app/api/routes.py:1-195`
- RSS fetcher: `apps/newsletter-backend/app/services/fetcher.py:1-135`
- LLM summarizer: `apps/newsletter-backend/app/services/summarizer.py:1-374`
- Newsletter generator: `apps/newsletter-backend/app/services/generator.py:1-115`
- Database models: `apps/newsletter-backend/app/models.py:1-63`
- LLM prompts: `apps/newsletter-backend/app/prompts.py:1-167`
- Configuration: `apps/newsletter-backend/config.py:1-70`
- HTML template: `apps/newsletter-backend/app/templates/newsletter.html:1-99`

**Configuration:**

- Dependencies: `apps/newsletter-backend/pyproject.toml:1-43`
- Environment example: `apps/newsletter-backend/.env.example`
- Project conventions: `/Users/jacob.lecoq.ext/Projects/ai_projects/newsletter-ai/CLAUDE.md`

**Frontend (Placeholder):**

- Main entry: `apps/web/src/main.ts:1-23`
- Package config: `apps/web/package.json`

### External References

**Newsletter Architecture & Design:**

- [Newsletter Design Best Practices 2025](https://tabular.email/blog/newsletter-design-best-practices)
- [8 Best Modern Newsletter Design](https://uicreative.net/blog/8-best-modern-newsletter-design-2025.html)
- [Software Architecture Best Practices](https://www.42coffeecups.com/blog/software-architecture-best-practices)

**RSS & Email Parsing:**

- [Maizzle RSS Feed Guide](https://maizzle.com/guides/rss-feed)
- [Python Email Parser Documentation](https://docs.python.org/3/library/email.parser.html)
- [Mailgun Flanker Library](https://www.mailgun.com/blog/product/we-just-open-sourced-flanker-our-python-email-address-and-mime-parsing-library/)

**AI Summarization:**

- [LLM Comparison 2025](https://www.ideas2it.com/blogs/llm-comparison)
- [Best LLMs for Summarization](https://visionvix.com/best-llm-for-summarization/)
- [LLM API Pricing Comparison](https://intuitionlabs.ai/articles/llm-api-pricing-comparison-2025)

**Performance & Caching:**

- [ByteByteGo Caching Strategies](https://blog.bytebytego.com/p/a-guide-to-top-caching-strategies)
- [Practical AsyncIO Guide](https://betterstack.com/community/guides/scaling-python/python-async-programming/)
- [FastAPI Async Documentation](https://fastapi.tiangolo.com/async/)

**Error Handling & Testing:**

- [FastAPI Exception Handling](https://betterstack.com/community/guides/scaling-python/error-handling-fastapi/)
- [Python Retry Logic Guide](https://pythonprograming.com/blog/mastering-retry-logic-in-python-best-practices-for-robust-api-calls)
- [Advanced Integration Testing 2025](https://moldstud.com/articles/p-advanced-integration-testing-techniques-for-python-developers-expert-guide-2025)
- [Real Python Pytest Guide](https://realpython.com/pytest-python-testing/)

**Framework Documentation:**

- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/docs/introduction/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Vite Documentation](https://vite.dev/)

### Related Work

**Similar Projects:**

- [Summate.io](https://summate.io/) - AI newsletter summarization service
- [FlipRSS](https://fliprss.com/rss-to-email/) - RSS to Email automation
- [Maizzle](https://maizzle.com/) - Email framework with RSS support

## Entity Relationship Diagram

```mermaid
erDiagram
    Subscriber ||--o{ NewsletterDelivery : receives
    Newsletter ||--o{ NewsletterDelivery : sent_to
    Newsletter ||--o{ NewsletterArticle : contains
    Article ||--o{ NewsletterArticle : included_in

    Subscriber {
        int id PK
        string email UK
        datetime subscribed_at
        boolean is_active
        json preferences
        datetime created_at
        datetime updated_at
    }

    Newsletter {
        int id PK
        string title
        text content
        datetime created_at
    }

    Article {
        int id PK
        string title
        string url UK
        text content
        text summary
        string source
        datetime published_date
        datetime created_at
        datetime updated_at
    }

    NewsletterArticle {
        int id PK
        int newsletter_id FK
        int article_id FK
        int display_order
    }

    NewsletterDelivery {
        int id PK
        int newsletter_id FK
        int subscriber_id FK
        datetime sent_at
        string status
        datetime opened_at
        datetime clicked_at
        string tracking_token
    }
```

## Next Steps

After creating this plan, you can:

1. **Start Implementation** - Run `/work` command with this plan file
2. **Get Expert Review** - Run `/plan_review` for feedback from specialized reviewers
3. **Create GitHub Issue** - Track progress in your issue tracker
4. **Simplify** - Reduce scope if this feels too comprehensive
5. **Rework** - Adjust approach based on your preferences

**Recommended First Step:** Run `/plan_review` to get feedback from DHH (Rails/simplicity), Kieran (quality standards), and the Simplicity reviewer before starting implementation. This will help validate the approach and catch any over-engineering.
