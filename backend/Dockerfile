# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files first (layer cache: only reinstall when deps change)
COPY backend/pyproject.toml backend/poetry.lock* ./

# Install production dependencies only — no virtualenv inside container
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (baked into image — no volume mounts in production)
COPY backend/app ./app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Production server: no --reload flag
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
