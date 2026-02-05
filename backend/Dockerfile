# OSRS Backend Dockerfile
# Multi-stage build for server and worker

FROM python:3.11-slim AS base

WORKDIR /app

# Ensure logs flush immediately to Docker
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy all source files needed for installation
COPY pyproject.toml ./
COPY src ./src

# Install the package (non-editable for Docker)
RUN pip install --no-cache-dir .

# Copy Prisma schema and generate client
COPY prisma ./prisma
RUN prisma generate

# ---------------------
# Server target
# ---------------------
FROM base AS server

EXPOSE 8080 9999

# Health check for the HTTP API
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "osrs_backend.main"]

# ---------------------
# Worker target
# ---------------------
FROM base AS worker

CMD ["python", "-m", "arq", "osrs_backend.workers.arq_worker.WorkerSettings"]
