# Graph Report - sectoral_api  (2026-10-04)

## Corpus Check
- 86 files · ~50,337 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 706 nodes · 1178 edges · 78 communities (47 shown, 26 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 116 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `32b89c09`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- tags.py
- app/page.js
- ChartlinkScraper
- screeners.py
- GeminiTagger
- RateLimiter
- What You Must Do When Invoked
- get_settings
- main.py
- WebhookAlert
- Stock
- What You Must Do When Invoked
- Quick Start (Local Development)
- package.json
- scheduler.py
- next.config.mjs
- 5.2 Table Definitions
- dashboard.py
- layout.js
- compilerOptions
- graphify reference: extra exports and benchmark
- env.py
- graphify reference: extra exports and benchmark
- Sectoral API — Stock Screener Tag & Returns Tracker
- lifespan
- 9. API Endpoints
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- 2. Technology Stack
- 6. AI-Powered Sector Tagging (Gemini)
- Settings
- 13. Deployment Guide (Render)
- 1. Project Overview
- graphify reference: add a URL and watch a folder
- render.yaml
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- frontend/README.md
- 10. Intraday Webhook Alerts
- 11. Scheduler & Cron Jobs
- 14. Scaling Considerations
- docker-compose.prod.yml
- docker-compose.yml
- app/__init__.py
- schemas/__init__.py
- services/__init__.py
- utils/__init__.py
- 16. Appendix
- 4. Data Extraction from Chartlink
- 7. Redis Caching Strategy
- 8. Weekly Returns Calculation
- Next.js Logo
- graphify reference: GitHub clone and cross-repo merge
- File Icon
- Globe Icon
- Window Icon
- sectoral-api
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- 3. System Architecture
- AGENTS.md
- rules/graphify.md
- workflows/graphify.md
- CLAUDE.md
- .claude/CLAUDE.md
- .claude/skills/graphify/references/extraction-spec.md
- .codex/skills/graphify/references/extraction-spec.md
- frontend/AGENTS.md
- eslint.config.mjs

## God Nodes (most connected - your core abstractions)
1. `Stock` - 38 edges
2. `DailySnapshot` - 31 edges
3. `get_settings()` - 24 edges
4. `GeminiTagger` - 24 edges
5. `Tag` - 20 edges
6. `StockTag` - 20 edges
7. `ReturnsCalculator` - 19 edges
8. `Sectoral API — Stock Screener Tag & Returns Tracker` - 19 edges
9. `RateLimiter` - 17 edges
10. `Screener` - 16 edges

## Surprising Connections (you probably didn't know these)
- `_enrich_tags_with_metrics()` --uses--> `TagDailyReturns`  [INFERRED]
  backend/app/routers/tags.py → backend/app/models/returns.py
- `get_tag_daily_returns()` --uses--> `TagDailyReturns`  [INFERRED]
  backend/app/routers/tags.py → backend/app/models/returns.py
- `get_stock_returns()` --uses--> `WeeklyReturns`  [INFERRED]
  backend/app/routers/stocks.py → backend/app/models/returns.py
- `_enrich_tags_with_metrics()` --uses--> `TagWeeklyReturns`  [INFERRED]
  backend/app/routers/tags.py → backend/app/models/returns.py
- `get_tag_returns()` --uses--> `TagWeeklyReturns`  [INFERRED]
  backend/app/routers/tags.py → backend/app/models/returns.py

## Import Cycles
- None detected.

## Communities (78 total, 26 thin omitted)

### Community 0 - "tags.py"
Cohesion: 0.11
Nodes (35): Junction linking a Stock to a Tag with provenance metadata. Tracks WHO tagged…, StockTag, _enrich_tags_with_metrics(), get_tag(), get_tag_daily_returns(), get_tag_returns(), get_tag_stocks(), list_tags() (+27 more)

### Community 1 - "app/page.js"
Cohesion: 0.11
Nodes (27): DashboardPage(), dynamic, dynamic, StocksPage(), dynamic, TagsPage(), TagDetailPage(), AdvanceDeclineBar() (+19 more)

### Community 2 - "ChartlinkScraper"
Cohesion: 0.13
Nodes (13): ChartlinkScraper, _find_column(), Chartlink screener scraper — data extraction from chartink.com. PATTERN:…, Run a Chartlink screener and return parsed stock data. Args: scan_clause: The…, Convert a raw Chartlink JSON row into our internal format. Chartlink's JSON…, Parse a Chartlink CSV export into ScrapedStock objects. This is the FALLBACK…, Close the underlying HTTP client., Find the first matching column name from a list of candidates. Returns None if… (+5 more)

### Community 3 - "screeners.py"
Cohesion: 0.12
Nodes (28): create_screener(), list_screeners(), AsyncSession, BaseModel, get, patch, post, Screener API router — manage and run Chartlink screeners. This router serves… (+20 more)

### Community 4 - "GeminiTagger"
Cohesion: 0.08
Nodes (24): format_sectors_for_prompt(), normalize_sector(), Format predefined sectors as a bulleted string for the Gemini prompt., Normalize and match a raw sector string to the predefined taxonomy. 1. Checks…, GeminiTagger, Any, AsyncSession, Generate (or retrieve cached) sector tags and classification for a stock.… (+16 more)

### Community 5 - "RateLimiter"
Cohesion: 0.15
Nodes (8): Redis, RateLimiter, How many daily requests are left., Current per-minute tokens (approximate — not refilled until acquire)., Async token-bucket rate limiter with per-minute and per-day limits. Thread-safe…, Add tokens proportional to elapsed time since last refill. If 6 seconds have…, Reset the daily counter if the calendar day (IST) has changed., Wait until a rate-limit token is available, then consume it. Raises…

### Community 6 - "What You Must Do When Invoked"
Cohesion: 0.07
Nodes (26): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+18 more)

### Community 7 - "get_settings"
Cohesion: 0.15
Nodes (15): get_settings(), Application configuration via Pydantic Settings. WHY Pydantic Settings? -…, Return a process-wide singleton Settings instance. Using @lru_cache so the .env…, Predefined sector taxonomy and normalization logic for stock classification., Async database engine and session factory. WHY async? - The API is I/O-heavy…, get_redis(), Redis, Async Redis client with lazy initialisation. WHY a module-level singleton? -… (+7 more)

### Community 8 - "main.py"
Cohesion: 0.12
Nodes (21): health_check(), get, FastAPI application entry-point. Responsibilities: 1. Wire up the lifespan…, Liveness probe — returns 200 if the server is up., FastAPI routers — mounted in app.main., Logging configuration for the Sectoral API. WHY configure logging explicitly? -…, Configure application-wide logging. Args: environment: 'development' for…, setup_logging() (+13 more)

### Community 9 - "WebhookAlert"
Cohesion: 0.10
Nodes (20): get_session(), AsyncSession, Yield an async DB session, then close it. Usage in routers:…, SQLModel, WebhookAlert model — intraday events from Chartlink alerts. Design decisions:…, An intraday alert event received from a Chartlink webhook., WebhookAlert, AsyncSession (+12 more)

### Community 10 - "Stock"
Cohesion: 0.05
Nodes (54): DailySnapshot, SQLModel, Stock and DailySnapshot models. Design decisions: ───────────────── Stock is…, Master stock record — one row per unique equity symbol., Point-in-time market data for a stock on a given day and screener. One row =…, Stock, get_stock(), get_stock_history() (+46 more)

### Community 11 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 12 - "Quick Start (Local Development)"
Cohesion: 0.13
Nodes (14): 1. Clone & Install, 2. Configure Environment, 3. Create the Database, 4. Run Migrations, 5. Start the Server, 6. Add Your First Screener, 7. Run the Smoke Test, API Documentation (+6 more)

### Community 13 - "package.json"
Cohesion: 0.10
Nodes (19): dependencies, next, react, react-dom, devDependencies, eslint, eslint-config-next, name (+11 more)

### Community 14 - "scheduler.py"
Cohesion: 0.25
Nodes (9): SQLModel, Screener model — stores Chartlink scan configurations. Each screener row…, A Chartlink screener configuration., Screener, backfill_stocks_in_background(), Background worker function to backfill 2-year history for newly discovered…, daily_screener_fetch(), APScheduler job definitions for automated data pipeline. PATTERN: Orchestrator… (+1 more)

### Community 16 - "5.2 Table Definitions"
Cohesion: 0.17
Nodes (12): 5.1 Entity Relationship Diagram, 5.2 Table Definitions, 5.3 Database Indexes, 5. Database Design, DAILY_SNAPSHOTS, SCREENERS, STOCK_TAGS, STOCKS (+4 more)

### Community 17 - "dashboard.py"
Cohesion: 0.08
Nodes (40): Database models barrel-export. WHY import all models here? - SQLAlchemy /…, SQLModel, Weekly returns models — pre-computed performance data. Design decisions:…, End-of-day aggregate return for all stocks carrying a tag., Pre-computed weekly return for a single stock. One row = one stock's…, Aggregated weekly return across all stocks sharing a tag. One row = one tag…, TagDailyReturns, TagWeeklyReturns (+32 more)

### Community 20 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 21 - "env.py"
Cohesion: 0.22
Nodes (10): do_run_migrations(), Alembic environment configuration — bridges Alembic with our app. KEY DESIGN…, Run migrations in 'offline' mode — generates SQL without connecting. Useful for…, Execute migrations using the provided connection., Run migrations through an async engine., Run migrations in 'online' mode — connects to the DB and applies changes., run_async_migrations(), run_migrations_offline() (+2 more)

### Community 22 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 23 - "Sectoral API — Stock Screener Tag & Returns Tracker"
Cohesion: 0.25
Nodes (7): 12. Project Structure, 15.1 Automated Tests, 15.2 Manual Verification Checklist, 15. Verification & Testing Plan, Project Documentation, Sectoral API — Stock Screener Tag & Returns Tracker, Table of Contents

### Community 24 - "lifespan"
Cohesion: 0.25
Nodes (8): init_db(), Create all tables from SQLModel metadata. Intended for development / first-run…, lifespan(), Manage startup and shutdown resources. Using the modern lifespan pattern…, close_redis(), Gracefully close the Redis connection pool. Called during application shutdown…, backfill_derived_returns(), Build new derived data from existing persistent snapshots after deploy.

### Community 25 - "9. API Endpoints"
Cohesion: 0.29
Nodes (7): 9.1 Stock APIs, 9.2 Tag APIs, 9.3 Screener APIs, 9.4 Webhook APIs, 9.5 Dashboard APIs, 9.6 Cache Management APIs, 9. API Endpoints

### Community 26 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 27 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 28 - "2. Technology Stack"
Cohesion: 0.33
Nodes (6): 2.1 Backend, 2.2 Frontend, 2.3 Infrastructure, 2.4 AI Model Decision Rationale, 2.5 Database Decision: Why Not a Time-Series Database?, 2. Technology Stack

### Community 29 - "6. AI-Powered Sector Tagging (Gemini)"
Cohesion: 0.33
Nodes (6): 6.1 Tagging Philosophy, 6.2 Prompt Template, 6.3 Example Input/Output, 6.4 Tag Generation Service Logic, 6.5 Rate Limiting, 6. AI-Powered Sector Tagging (Gemini)

### Community 30 - "Settings"
Cohesion: 0.40
Nodes (4): Central configuration read from environment variables / .env file., Fix DATABASE_URL scheme for Render compatibility. Render provides postgres://…, Settings, BaseSettings

### Community 31 - "13. Deployment Guide (Render)"
Cohesion: 0.40
Nodes (5): 13.1 Services Overview, 13.2 Render Blueprint (render.yaml), 13.3 Environment Variables, 13.4 Deployment Steps, 13. Deployment Guide (Render)

### Community 32 - "1. Project Overview"
Cohesion: 0.40
Nodes (5): 1.1 Problem Statement, 1.2 Solution, 1.3 Target Scale, 1.4 High-Level Flow, 1. Project Overview

### Community 33 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 34 - "render.yaml"
Cohesion: 0.60
Nodes (4): Backend Service, Frontend Service, Postgres Service, Redis Service

### Community 35 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 36 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 37 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 38 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 39 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 40 - "frontend/README.md"
Cohesion: 0.50
Nodes (3): Deploy on Vercel, Getting Started, Learn More

### Community 41 - "10. Intraday Webhook Alerts"
Cohesion: 0.50
Nodes (4): 10.1 Alert Flow, 10.2 Alert Configuration, 10.3 Alert Types (Examples), 10. Intraday Webhook Alerts

### Community 42 - "11. Scheduler & Cron Jobs"
Cohesion: 0.50
Nodes (4): 11.1 Job Schedule, 11.2 APScheduler Configuration, 11.3 Render Free Tier Caveat, 11. Scheduler & Cron Jobs

### Community 43 - "14. Scaling Considerations"
Cohesion: 0.50
Nodes (4): 14.1 Current Architecture Capacity, 14.2 Scaling Path (When Needed), 14.3 Key Design Decisions for Scale, 14. Scaling Considerations

### Community 44 - "docker-compose.prod.yml"
Cohesion: 0.83
Nodes (3): Backend Service, Postgres Service, Redis Service

### Community 50 - "16. Appendix"
Cohesion: 0.50
Nodes (4): 16.1 Python Dependencies (requirements.txt), 16.2 Key API Rate Limits Reference, 16.3 Glossary, 16. Appendix

### Community 51 - "4. Data Extraction from Chartlink"
Cohesion: 0.50
Nodes (4): 4.1 Layer 1: POST Simulation (Primary — Daily Bulk Fetch), 4.2 Layer 2: Webhook Alerts (Secondary — Intraday Event Triggers), 4.3 Layer 3: CSV Upload (Fallback), 4. Data Extraction from Chartlink

### Community 52 - "7. Redis Caching Strategy"
Cohesion: 0.50
Nodes (4): 7.1 Cache Keys, 7.2 Cache Flow Diagram, 7.3 Cache Invalidation, 7. Redis Caching Strategy

### Community 53 - "8. Weekly Returns Calculation"
Cohesion: 0.50
Nodes (4): 8.1 Per-Stock Weekly Return, 8.2 Per-Tag Aggregated Return, 8.3 Example Output, 8. Weekly Returns Calculation

### Community 64 - "3. System Architecture"
Cohesion: 0.67
Nodes (3): 3.1 Component Diagram, 3.2 Data Flow Summary, 3. System Architecture

## Knowledge Gaps
- **198 isolated node(s):** `sectoral-api`, `metadata`, `dynamic`, `dynamic`, `dynamic` (+193 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 420 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Stock` connect `Stock` to `tags.py`, `screeners.py`, `GeminiTagger`, `get_settings`, `WebhookAlert`, `scheduler.py`, `dashboard.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `DailySnapshot` connect `Stock` to `tags.py`, `screeners.py`, `GeminiTagger`, `get_settings`, `scheduler.py`, `dashboard.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `ReturnsCalculator` connect `dashboard.py` to `tags.py`, `lifespan`, `Stock`, `scheduler.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Stock` (e.g. with `get_dashboard()` and `run_screener()`) actually correct?**
  _`Stock` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `DailySnapshot` (e.g. with `get_dashboard()` and `run_screener()`) actually correct?**
  _`DailySnapshot` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `GeminiTagger` (e.g. with `DailySnapshot` and `Stock`) actually correct?**
  _`GeminiTagger` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Tag` (e.g. with `get_dashboard()` and `get_stock()`) actually correct?**
  _`Tag` has 10 INFERRED edges - model-reasoned connections that need verification._