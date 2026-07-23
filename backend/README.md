# Sectoral API

Stock screener tag & returns tracker for Indian equities.

Scrapes Chartlink screeners daily, auto-tags stocks with Gemini AI,
and computes weekly returns by stock and sector tag.

## Quick Start (Local Development)

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Gemini API key ([get one here](https://aistudio.google.com/apikey))

### 1. Clone & Install

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual values:
#   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/sectoral_db
#   REDIS_URL=redis://localhost:6379/0
#   GEMINI_API_KEY=your_key_here
```

### 3. Create the Database

```bash
createdb sectoral_db        # or use pgAdmin / DBeaver
```

### 4. Run Migrations

```bash
# Generate initial migration (first time only):
alembic revision --autogenerate -m "initial tables"

# Apply migrations:
alembic upgrade head
```

### 5. Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit:
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

### 6. Add Your First Screener

```bash
curl -X POST http://localhost:8000/api/screeners \
  -H "Content-Type: application/json" \
  -d '{"name": "Volume Breakouts", "scan_clause": "( {cash} ( latest close > latest sma( close, 200 ) ) )"}'
```

### 7. Run the Smoke Test

```bash
python smoke_test.py
```

## Deploy to Render

1. Push this repo to GitHub.
2. Go to [Render Blueprints](https://dashboard.render.com/blueprints).
3. Click **New Blueprint Instance** and connect your repo.
4. Render reads `render.yaml` and creates everything (web service + PostgreSQL + Redis).
5. Set `GEMINI_API_KEY` in the Render dashboard (Environment → Secret).

## API Documentation

Once running, interactive API docs are at `/docs` (Swagger UI) or `/redoc`.

See [Sectoral_API_Documentation.md](./Sectoral_API_Documentation.md) for the full technical spec.

## Architecture

```
backend/app/
├── config.py           # Pydantic Settings (env-driven)
├── database.py         # Async SQLAlchemy engine
├── redis_client.py     # Async Redis singleton
├── main.py             # FastAPI app + lifespan
├── models/             # SQLModel database models
├── schemas/            # Pydantic response schemas
├── routers/            # HTTP endpoints (thin)
├── services/           # Business logic (thick)
│   ├── chartlink_scraper.py   # POST simulation + CSV fallback
│   ├── gemini_tagger.py       # Cache-aside tagging
│   ├── returns_calculator.py  # Weekly batch computation
│   ├── scheduler.py           # APScheduler cron jobs
│   └── webhook_handler.py     # Intraday alert handler
└── utils/
    ├── rate_limiter.py        # Token-bucket for Gemini
    └── logging_config.py      # Structured logging
```

## License

Private — not licensed for redistribution.
