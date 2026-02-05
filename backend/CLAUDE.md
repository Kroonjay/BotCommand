# Backend - Production API Server

## Overview

The unified production server providing HTTP API and TCP ML inference for BotScript clients.

## Quick Start

```bash
pip install -e .
osrs serve              # HTTP :8080 + TCP :5555
osrs serve --http-only  # HTTP only
osrs serve --tcp-only   # TCP only
osrs worker             # Background job worker
```

## Structure

```
src/osrs_backend/
├── main.py             # Unified entry point (FastAPI + TCP)
├── cli.py              # Click CLI commands
├── config.py           # Pydantic settings
│
├── api/                # HTTP layer
│   ├── app.py          # FastAPI app factory
│   └── routers/
│       ├── items.py    # /items/* endpoints
│       ├── tasks.py    # /tasks/* endpoints
│       └── healthcheck.py
│
├── tcp/                # TCP layer
│   ├── server.py       # asyncio TCP server
│   └── protocol.py     # Request/response handling
│
├── services/           # Business logic
│   ├── inference.py    # Model prediction
│   ├── items.py        # Item lookups
│   └── prices.py       # GE prices
│
├── ml/                 # ML utilities
│   ├── model_loader.py # Load .zip models
│   └── remote_processor.py
│
├── db/                 # Database
│   ├── database.py     # Prisma client
│   └── prisma/         # Schema
│
└── workers/            # Background jobs
    └── arq_worker.py   # ARQ tasks
```

## Adding a New HTTP Endpoint

1. Create router file:
```python
# src/osrs_backend/api/routers/myrouter.py
from fastapi import APIRouter

router = APIRouter(prefix="/my", tags=["my"])

@router.get("/endpoint")
async def my_endpoint():
    return {"status": "ok"}
```

2. Register in app.py:
```python
from osrs_backend.api.routers import myrouter
app.include_router(myrouter.router)
```

## TCP Protocol

Newline-delimited JSON on port 5555:

```json
// Request
{"obs": [[0.5, 0.3, ...]], "actionMasks": [[true, true, ...]], "deterministic": true}

// Response
{"action": [1, 0, 3, ...]}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost` | Redis for ARQ |
| `MODEL_PATH` | - | Path to model .zip |
| `HTTP_PORT` | `8080` | FastAPI port |
| `TCP_PORT` | `5555` | Inference port |

## Testing

```bash
pytest tests/
```
