# Stage 1 — Builder
FROM ghcr.io/astral-sh/uv:0.6-python3.12-bookworm-slim AS builder

WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies only
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY backend/ backend/
COPY frontend/ frontend/

# Install project
RUN uv sync --frozen --no-dev

# Stage 2 — Runtime
FROM python:3.12-slim-bookworm

WORKDIR /app

# Create non-root user
RUN groupadd --system app && useradd --system --gid app app

# Create data directory for SQLite
RUN mkdir /data && chown app:app /data

# Copy virtual environment and application code from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/backend /app/backend
COPY --from=builder /app/frontend /app/frontend
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

# Use venv Python
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:////data/bid_exchange.db

EXPOSE 8000

USER app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
