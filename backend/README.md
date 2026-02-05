# OSRS Backend

Unified backend server for OSRS ML inference and bot command API.

## Services

- **HTTP API** (port 8080): FastAPI server for items, actions, tasks, and healthcheck
- **TCP Server** (port 9999): Low-latency ML model inference
- **ARQ Worker**: Background jobs for price fetching and data processing

## Quick Start

### Local Development

```bash
# Install dependencies
pipenv install -e .

# Generate Prisma client
prisma generate

# Start server
python -m osrs_backend.main

# Or use CLI
osrs serve
```

### Docker Compose

```bash
# Build and start all services
docker compose up --build

# Start in detached mode
docker compose up -d

# View logs
docker compose logs -f server
```

## Environment Variables

Copy `.env.example` to `.env` and configure as needed. Key variables:

- `POSTGRES_PRISMA_URL`: PostgreSQL connection string
- `REDIS_HOST`/`REDIS_PORT`: Redis connection for ARQ
- `HTTP_PORT`: HTTP API port (default: 8080)
- `TCP_PORT`: TCP inference port (default: 9999)
- `MODELS_DIR`: Directory for ML model files

## CLI Commands

```bash
osrs serve              # Start HTTP + TCP server
osrs serve --http-only  # HTTP only
osrs serve --tcp-only   # TCP only
osrs worker             # Start ARQ background worker
```
