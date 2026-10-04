# Graph Report - sectoral_api  (2026-09-12)

## Corpus Check
- Corpus is ~48,035 words - fits in a single context window. You may not need a graph.

## Summary
- 644 nodes · 1369 edges · 61 communities (44 shown, 15 thin omitted)
- Extraction: 69% EXTRACTED · 31% INFERRED · 0% AMBIGUOUS · INFERRED: 431 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Returns Calculator Engine
- Sector Heatmap Components
- Chartlink Scraper Service
- Graphify Tooling 3
- Gemini Sector Tagger
- Gemini Sector Tagger (2)
- Graphify Tooling 6
- Gemini Sector Tagger (3)
- Scheduler & Cron Jobs
- Chartlink Scraper Service (2)
- Sector Heatmap Components (2)
- Database Session & Migrations
- Chartlink Scraper Service (3)
- App Configuration & Environment
- Gemini Sector Tagger (4)
- Chartlink Scraper Service (4)
- App Configuration & Environment (2)
- Returns Calculator Engine (2)
- Frontend Application & UI
- App Configuration & Environment (3)
- Webhook Alerts & Processing
- App Configuration & Environment (4)
- Graphify Tooling 22
- Screener Management & Models
- Scheduler & Cron Jobs (2)
- Graphify Tooling 25
- Graphify Tooling 26
- Webhook Alerts & Processing (2)
- Database Session & Migrations (2)
- Gemini Sector Tagger (5)
- Graphify Tooling 30
- Graphify Tooling 31
- Docker & Deployment Infrastructure
- Project Architecture Documentation
- Redis Caching Layer
- Gemini Sector Tagger (6)
- Graphify Tooling 36
- Webhook Alerts & Processing (3)
- Scheduler & Cron Jobs (3)
- Project Architecture Documentation (2)
- Project Dependencies & Packages
- Chartlink Scraper Service (5)
- Redis Caching Layer (2)
- Returns & Analytics Models
- Redis Caching Layer (3)
- Redis Caching Layer (4)
- Screener Management & Models (2)
- Schemas Module
- Services Module
- Utils Module
- Graphify Tooling 50
- Graphify Tooling 51
- Graphify Tooling 52
- Graphify Tooling 53
- Next Module
- Icon Module
- Globe Module
- Window Module
- Sectoral Module

## God Nodes (most connected - your core abstractions)
1. `Stock` - 32 edges
2. `DailySnapshot` - 25 edges
3. `get_settings()` - 24 edges
4. `GeminiTagger` - 22 edges
5. `StockTag` - 21 edges
6. `Tag` - 20 edges
7. `ReturnsCalculator` - 19 edges
8. `Sectoral API — Stock Screener Tag & Returns Tracker` - 19 edges
9. `get_session()` - 18 edges
10. `get_dashboard()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `get_stock_returns()` --uses--> `WeeklyReturns`  [INFERRED]
  backend/app/routers/stocks.py → backend/app/models/returns.py
- `create_screener()` --uses--> `Screener`  [INFERRED]
  backend/app/routers/screeners.py → backend/app/models/screener.py
- `list_screeners()` --uses--> `Screener`  [INFERRED]
  backend/app/routers/screeners.py → backend/app/models/screener.py
- `update_screener()` --uses--> `Screener`  [INFERRED]
  backend/app/routers/screeners.py → backend/app/models/screener.py
- `upload_csv()` --uses--> `Screener`  [INFERRED]
  backend/app/routers/screeners.py → backend/app/models/screener.py

## Import Cycles
- None detected.

## Communities (61 total, 15 thin omitted)

### Community 0 - "Returns Calculator Engine"
Cohesion: 0.06
Nodes (64): SQLModel, Weekly returns models — pre-computed performance data. Design decisions:…, End-of-day aggregate return for all stocks carrying a tag., Pre-computed weekly return for a single stock. One row = one stock's…, Aggregated weekly return across all stocks sharing a tag. One row = one tag…, TagDailyReturns, TagWeeklyReturns, WeeklyReturns (+56 more)

### Community 1 - "Sector Heatmap Components"
Cohesion: 0.11
Nodes (27): DashboardPage(), dynamic, dynamic, StocksPage(), dynamic, TagsPage(), TagDetailPage(), AdvanceDeclineBar() (+19 more)

### Community 2 - "Chartlink Scraper Service"
Cohesion: 0.07
Nodes (31): create_screener(), list_screeners(), AsyncSession, BaseModel, get, post, List all configured screeners., Add a new Chartlink screener configuration. (+23 more)

### Community 3 - "Graphify Tooling 3"
Cohesion: 0.08
Nodes (26): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+18 more)

### Community 4 - "Gemini Sector Tagger"
Cohesion: 0.13
Nodes (15): GeminiTagger, AsyncSession, Generate (or retrieve cached) sector tags for a stock. Returns: List of 3…, Batch process tags for multiple stocks. Args: stocks_info: List of (Stock,…, Call Gemini API with rate limiting and response parsing. Retries up to 3 times…, Parse Gemini's response into exactly 3 normalised tag strings. Gemini should…, Fetch current tags for a stock from the database., Get the most recent LTP for a stock from daily_snapshots. (+7 more)

### Community 5 - "Gemini Sector Tagger (2)"
Cohesion: 0.11
Nodes (17): SQLModel, Screener model — stores Chartlink scan configurations. Each screener row…, A Chartlink screener configuration., Screener, Screener API router — manage and run Chartlink screeners. This router serves…, Manually run a screener NOW (bypasses the 6:30 PM schedule). Pipeline: 1. Fetch…, Response from running a screener., Run Gemini tagging in the background after the API responds. This respects rate… (+9 more)

### Community 6 - "Graphify Tooling 6"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 7 - "Gemini Sector Tagger (3)"
Cohesion: 0.15
Nodes (15): get_settings(), Application configuration via Pydantic Settings. WHY Pydantic Settings? -…, Central configuration read from environment variables / .env file., Fix DATABASE_URL scheme for Render compatibility. Render provides postgres://…, Return a process-wide singleton Settings instance. Using @lru_cache so the .env…, Settings, Async database engine and session factory. WHY async? - The API is I/O-heavy…, get_redis() (+7 more)

### Community 8 - "Scheduler & Cron Jobs"
Cohesion: 0.14
Nodes (19): init_db(), Create all tables from SQLModel metadata. Intended for development / first-run…, FastAPI application entry-point. Responsibilities: 1. Wire up the lifespan…, FastAPI routers — mounted in app.main., Configure application-wide logging. Args: environment: 'development' for…, setup_logging(), alembic, apscheduler (+11 more)

### Community 9 - "Chartlink Scraper Service (2)"
Cohesion: 0.15
Nodes (16): SQLModel, WebhookAlert model — intraday events from Chartlink alerts. Design decisions:…, An intraday alert event received from a Chartlink webhook., WebhookAlert, AsyncSession, post, Webhook receiver — accepts intraday alert payloads from Chartlink. WHY a…, Receive and process an intraday alert from Chartlink. Accepts raw JSON, parses… (+8 more)

### Community 10 - "Sector Heatmap Components (2)"
Cohesion: 0.17
Nodes (19): get_stock(), get_stock_history(), get_stock_returns(), list_stocks(), AsyncSession, get, Stock API router — CRUD and history for tracked stocks. PATTERN: Thin Router…, Get detailed info for a single stock, including tags and latest snapshot. (+11 more)

### Community 11 - "Database Session & Migrations"
Cohesion: 0.13
Nodes (13): get_session(), AsyncSession, Yield an async DB session, then close it. Usage in routers:…, graphify, graphify reference: extraction subagent prompt, For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration (+5 more)

### Community 12 - "Chartlink Scraper Service (3)"
Cohesion: 0.21
Nodes (8): Pydantic schemas for Returns / Dashboard API responses., Close the underlying HTTP client., Backfill daily sector rows from snapshots already in production., Materialize end-of-day sector performance for one market date. Daily snapshots…, backfill_derived_returns(), Build new derived data from existing persistent snapshots after deploy., Current per-minute tokens (approximate — not refilled until acquire)., Add tokens proportional to elapsed time since last refill. If 6 seconds have…

### Community 13 - "App Configuration & Environment"
Cohesion: 0.12
Nodes (14): This is NOT the Next.js you know, dependencies, next, react, react-dom, devDependencies, eslint, eslint-config-next (+6 more)

### Community 14 - "Gemini Sector Tagger (4)"
Cohesion: 0.24
Nodes (11): Database models barrel-export. WHY import all models here? - SQLAlchemy /…, DailySnapshot, SQLModel, Stock and DailySnapshot models. Design decisions: ───────────────── Stock is…, Master stock record — one row per unique equity symbol., Point-in-time market data for a stock on a given day and screener. One row =…, Stock, Gemini-powered sector/industry tag generator with Redis caching. PATTERN:… (+3 more)

### Community 15 - "Chartlink Scraper Service (4)"
Cohesion: 0.22
Nodes (6): close_redis(), Gracefully close the Redis connection pool. Called during application shutdown…, GET the Chartlink homepage and extract the CSRF token. Chartlink embeds a CSRF…, Logging configuration for the Sectoral API. WHY configure logging explicitly? -…, eslintConfig, nextConfig

### Community 16 - "App Configuration & Environment (2)"
Cohesion: 0.14
Nodes (14): 1. Clone & Install, 2. Configure Environment, 3. Create the Database, 4. Run Migrations, 5. Start the Server, 6. Add Your First Screener, 7. Run the Smoke Test, API Documentation (+6 more)

### Community 17 - "Returns Calculator Engine (2)"
Cohesion: 0.30
Nodes (7): AsyncSession, Calculate available completed weeks, oldest first, idempotently., Compute weekly return for every stock that has snapshots in the range. For each…, Aggregate weekly returns by tag. For each tag: 1. Find all stocks linked to…, Get the Monday-to-Friday range of the most recent complete trading week. If…, Run the full weekly returns pipeline. Args: session: Async database session.…, date

### Community 18 - "Frontend Application & UI"
Cohesion: 0.18
Nodes (8): For /graphify add, For --watch, graphify reference: add a URL and watch a folder, For /graphify add, For --watch, graphify reference: add a URL and watch a folder, metadata, start

### Community 19 - "App Configuration & Environment (3)"
Cohesion: 0.18
Nodes (9): graphify reference: transcribe video and audio, Step 2.5 - Transcribe video / audio files (only if video files detected), graphify reference: transcribe video and audio, Step 2.5 - Transcribe video / audio files (only if video files detected), compilerOptions, paths, scripts, dev (+1 more)

### Community 20 - "Webhook Alerts & Processing"
Cohesion: 0.17
Nodes (12): 5.1 Entity Relationship Diagram, 5.2 Table Definitions, 5.3 Database Indexes, 5. Database Design, DAILY_SNAPSHOTS, SCREENERS, STOCK_TAGS, STOCKS (+4 more)

### Community 21 - "App Configuration & Environment (4)"
Cohesion: 0.22
Nodes (10): do_run_migrations(), Alembic environment configuration — bridges Alembic with our app. KEY DESIGN…, Run migrations in 'offline' mode — generates SQL without connecting. Useful for…, Execute migrations using the provided connection., Run migrations through an async engine., Run migrations in 'online' mode — connects to the DB and applies changes., run_async_migrations(), run_migrations_offline() (+2 more)

### Community 22 - "Graphify Tooling 22"
Cohesion: 0.18
Nodes (9): health_check(), get, Liveness probe — returns 200 if the server is up., For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only, Deploy on Vercel, Getting Started (+1 more)

### Community 23 - "Screener Management & Models"
Cohesion: 0.20
Nodes (10): 12. Project Structure, 15.1 Automated Tests, 15.2 Manual Verification Checklist, 15. Verification & Testing Plan, 3.1 Component Diagram, 3.2 Data Flow Summary, 3. System Architecture, Project Documentation (+2 more)

### Community 24 - "Scheduler & Cron Jobs (2)"
Cohesion: 0.22
Nodes (9): lifespan(), Manage startup and shutdown resources. Using the modern lifespan pattern…, cleanup_old_snapshots(), Compute weekly returns for all stocks and tag cohorts. Called every Monday at…, Delete daily_snapshots older than SNAPSHOT_RETENTION_DAYS. Called every Sunday…, Register all scheduled jobs on the module-level scheduler. Called once during…, register_jobs(), weekly_returns_calc() (+1 more)

### Community 25 - "Graphify Tooling 25"
Cohesion: 0.25
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 26 - "Graphify Tooling 26"
Cohesion: 0.25
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 27 - "Webhook Alerts & Processing (2)"
Cohesion: 0.29
Nodes (7): 9.1 Stock APIs, 9.2 Tag APIs, 9.3 Screener APIs, 9.4 Webhook APIs, 9.5 Dashboard APIs, 9.6 Cache Management APIs, 9. API Endpoints

### Community 28 - "Database Session & Migrations (2)"
Cohesion: 0.33
Nodes (6): 2.1 Backend, 2.2 Frontend, 2.3 Infrastructure, 2.4 AI Model Decision Rationale, 2.5 Database Decision: Why Not a Time-Series Database?, 2. Technology Stack

### Community 29 - "Gemini Sector Tagger (5)"
Cohesion: 0.33
Nodes (6): 6.1 Tagging Philosophy, 6.2 Prompt Template, 6.3 Example Input/Output, 6.4 Tag Generation Service Logic, 6.5 Rate Limiting, 6. AI-Powered Sector Tagging (Gemini)

### Community 30 - "Graphify Tooling 30"
Cohesion: 0.40
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 31 - "Graphify Tooling 31"
Cohesion: 0.40
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 32 - "Docker & Deployment Infrastructure"
Cohesion: 0.40
Nodes (5): 13.1 Services Overview, 13.2 Render Blueprint (render.yaml), 13.3 Environment Variables, 13.4 Deployment Steps, 13. Deployment Guide (Render)

### Community 33 - "Project Architecture Documentation"
Cohesion: 0.40
Nodes (5): 1.1 Problem Statement, 1.2 Solution, 1.3 Target Scale, 1.4 High-Level Flow, 1. Project Overview

### Community 34 - "Redis Caching Layer"
Cohesion: 0.60
Nodes (4): Backend Service, Frontend Service, Postgres Service, Redis Service

### Community 36 - "Graphify Tooling 36"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 37 - "Webhook Alerts & Processing (3)"
Cohesion: 0.50
Nodes (4): 10.1 Alert Flow, 10.2 Alert Configuration, 10.3 Alert Types (Examples), 10. Intraday Webhook Alerts

### Community 38 - "Scheduler & Cron Jobs (3)"
Cohesion: 0.50
Nodes (4): 11.1 Job Schedule, 11.2 APScheduler Configuration, 11.3 Render Free Tier Caveat, 11. Scheduler & Cron Jobs

### Community 39 - "Project Architecture Documentation (2)"
Cohesion: 0.50
Nodes (4): 14.1 Current Architecture Capacity, 14.2 Scaling Path (When Needed), 14.3 Key Design Decisions for Scale, 14. Scaling Considerations

### Community 40 - "Project Dependencies & Packages"
Cohesion: 0.50
Nodes (4): 16.1 Python Dependencies (requirements.txt), 16.2 Key API Rate Limits Reference, 16.3 Glossary, 16. Appendix

### Community 41 - "Chartlink Scraper Service (5)"
Cohesion: 0.50
Nodes (4): 4.1 Layer 1: POST Simulation (Primary — Daily Bulk Fetch), 4.2 Layer 2: Webhook Alerts (Secondary — Intraday Event Triggers), 4.3 Layer 3: CSV Upload (Fallback), 4. Data Extraction from Chartlink

### Community 42 - "Redis Caching Layer (2)"
Cohesion: 0.50
Nodes (4): 7.1 Cache Keys, 7.2 Cache Flow Diagram, 7.3 Cache Invalidation, 7. Redis Caching Strategy

### Community 43 - "Returns & Analytics Models"
Cohesion: 0.50
Nodes (4): 8.1 Per-Stock Weekly Return, 8.2 Per-Tag Aggregated Return, 8.3 Example Output, 8. Weekly Returns Calculation

### Community 44 - "Redis Caching Layer (3)"
Cohesion: 0.83
Nodes (3): Backend Service, Postgres Service, Redis Service

## Knowledge Gaps
- **192 isolated node(s):** `sectoral-api`, `dynamic`, `dynamic`, `dynamic`, `eslintConfig` (+187 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 358 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Sectoral API — Stock Screener Tag & Returns Tracker` connect `Screener Management & Models` to `Docker & Deployment Infrastructure`, `Project Architecture Documentation`, `Webhook Alerts & Processing (3)`, `Scheduler & Cron Jobs (3)`, `Project Architecture Documentation (2)`, `Project Dependencies & Packages`, `Chartlink Scraper Service (2)`, `Chartlink Scraper Service (5)`, `Redis Caching Layer (2)`, `Returns & Analytics Models`, `Webhook Alerts & Processing`, `Webhook Alerts & Processing (2)`, `Database Session & Migrations (2)`, `Gemini Sector Tagger (5)`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Why does `react` connect `Sector Heatmap Components` to `App Configuration & Environment`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Why does `scripts` connect `App Configuration & Environment (3)` to `Gemini Sector Tagger (3)`, `Chartlink Scraper Service (2)`, `Database Session & Migrations`, `Chartlink Scraper Service (3)`, `App Configuration & Environment`, `Chartlink Scraper Service (4)`, `Frontend Application & UI`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Stock` (e.g. with `get_dashboard()` and `run_screener()`) actually correct?**
  _`Stock` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `DailySnapshot` (e.g. with `get_dashboard()` and `run_screener()`) actually correct?**
  _`DailySnapshot` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `get_settings()` (e.g. with `backend/README.md` and `Sectoral_API_Documentation.md`) actually correct?**
  _`get_settings()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `GeminiTagger` (e.g. with `DailySnapshot` and `Stock`) actually correct?**
  _`GeminiTagger` has 5 INFERRED edges - model-reasoned connections that need verification._