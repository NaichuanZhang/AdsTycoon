# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AdsTycoon** is an AI-powered real-time ad auction simulator. LLM agents (via AWS Bedrock + Strands SDK) generate simulation data, make bidding decisions, provide consumer feedback, and produce campaign insights — all streamed to the browser via SSE.

## Commands

```bash
# Install dependencies
uv sync

# Run dev server (port 8000 by default)
./run.sh
./run.sh 8001          # custom port

# Tests
uv run pytest --tb=short -q          # all tests
uv run pytest backend/tests/test_models.py -v  # single file
uv run pytest -k "test_create_consumer" -v     # single test by name
uv run pytest --cov=backend          # with coverage
uv run pytest -m integration         # bedrock integration tests (needs AWS creds)

# End-to-end demo (requires running server)
python demo.py --rounds 5 --consumers 30 --campaigns 6
```

No linter or formatter is configured.

## Architecture

### Backend (FastAPI + SQLAlchemy + Strands Agents)

**Data flow:** User creates simulation → Seeder agent generates consumers/websites/campaigns → Auction engine runs N rounds → Campaign agents bid → Consumer agents give feedback → Insights agent analyzes.

**Agent pattern:** Each agent module (`backend/agents/`) defines a system prompt. Corresponding tools (`backend/tools/`) are plain functions decorated with `@tool`. A session factory is set via `set_session_factory()` before each agent invocation — each tool call creates its own DB session to avoid corruption from parallel Strands tool calls.

**Streaming:** `backend/routers/stream.py` has three SSE endpoints (`/seed`, `/run`, `/insights/{campaign_id}`) that create agents inline, iterate `agent.stream_async()`, and yield formatted SSE events.

**Database:** SQLite via SQLAlchemy (sync sessions). Schema auto-created on startup via `Base.metadata.create_all()`. No migrations. Models: `Simulation → Consumer, Website, Campaign, Auction → Bid`.

**Config:** Environment variables with defaults in `backend/config.py`:
- `AWS_PROFILE` (default: `tokenmaster`)
- `AWS_REGION` (default: `us-east-1`)
- `BEDROCK_MODEL_ID` (default: `us.anthropic.claude-haiku-4-5-20251001-v1:0`)

### Frontend (Vanilla JS, no build step)

Static files served by FastAPI at `/`. ES6 modules in `frontend/js/` with class-based components. SSE via `EventSource` in `api.js`.

## Key Patterns

- **Idempotent seeder tools:** `create_consumers`, `create_websites`, `create_campaigns` check if data already exists for the simulation before inserting. This guards against LLM retry behavior during streaming.
- **Tool error recovery:** All DB-writing tools wrap commits in try/except and call `db.rollback()` on failure, returning error strings instead of raising — prevents session corruption from cascading.
- **Stream error handlers** also call `db.rollback()` before yielding error SSE events.
- **UUIDs as strings** for all primary keys.

## Testing

Tests in `backend/tests/`. Fixtures in `conftest.py` provide `db_session` (in-memory SQLite), `db_session_factory` (sessionmaker for tool tests), and `client` (FastAPI TestClient with DB override). Integration tests requiring AWS credentials are marked `@pytest.mark.integration`.
