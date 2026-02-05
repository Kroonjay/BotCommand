# BotCommand - OSRS Bot Infrastructure

## Overview

BotCommand is a monorepo containing all server-side infrastructure for OSRS bot automation:

| Component | Purpose | Language |
|-----------|---------|----------|
| `backend/` | Production API + ML inference server | Python |
| `pvp-ml/` | RL training framework (PPO, self-play) | Python |
| `simulation-rsps/` | Private server for training simulations | Java |
| `contracts/` | Shared environment specifications | JSON |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRODUCTION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   BotScript (DreamBot)              BotCommand/backend                       │
│   ┌─────────────────┐               ┌─────────────────┐                     │
│   │  Java Client    │──── HTTP ────►│  FastAPI        │                     │
│   │  (Real OSRS)    │               │  /items, /tasks │                     │
│   │                 │──── TCP ─────►│  ML Inference   │                     │
│   └─────────────────┘               │  (Port 5555)    │                     │
│                                     └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              TRAINING (Offline)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   simulation-rsps                   pvp-ml                                   │
│   ┌─────────────────┐               ┌─────────────────┐                     │
│   │  Elvarg Server  │◄── Socket ───►│  PPO Training   │                     │
│   │  (Simulated)    │   Port 7070   │  Self-play      │                     │
│   │                 │               │  Callbacks      │                     │
│   └─────────────────┘               └─────────────────┘                     │
│                                            │                                 │
│                                            ▼                                 │
│                                     models/*.zip                             │
│                                     (Trained agents)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Related Repository

- **BotScript** (`/Users/scoutfullner/dev/BotScript`) - Java DreamBot client that connects to this backend

## Quick Start

### Production Server (backend/)

```bash
cd backend
pip install -e .
osrs serve              # Start HTTP + TCP server
osrs serve --http-only  # HTTP only (port 8080)
osrs serve --tcp-only   # TCP only (port 5555)
osrs worker             # Start background job worker
```

### Training (pvp-ml/ + simulation-rsps/)

```bash
# Start simulation server
cd simulation-rsps/ElvargServer
TRAIN=true REMOTE_ENV_PORT=7070 ./gradlew run

# In another terminal, start training
cd pvp-ml
conda env create -f environment.yml
conda activate osrs
pip install -e .
train --preset config/nh/core.yml --experiment MyExperiment
```

### Serve Trained Model

```bash
# From pvp-ml
serve-api --model models/FineTunedNh.zip --port 5555
```

## Directory Structure

```
BotCommand/
├── backend/                    # Production server
│   ├── src/osrs_backend/
│   │   ├── api/               # FastAPI HTTP endpoints
│   │   │   └── routers/       # /items, /tasks, /healthcheck
│   │   ├── tcp/               # TCP inference server
│   │   ├── services/          # Business logic
│   │   ├── ml/                # Model loading utilities
│   │   ├── db/                # Prisma database
│   │   └── workers/           # ARQ background jobs
│   └── pyproject.toml
│
├── pvp-ml/                     # Training framework
│   ├── pvp_ml/
│   │   ├── env/               # Gymnasium environments
│   │   ├── ppo/               # PPO algorithm
│   │   ├── callback/          # Training callbacks
│   │   └── config/            # Training presets
│   ├── models/                # Trained model files
│   └── experiments/           # Training runs
│
├── simulation-rsps/            # Training RSPS
│   └── ElvargServer/
│       └── src/main/java/
│           ├── com/elvarg/    # Base server
│           └── com/github/naton1/rl/  # RL plugin
│
└── contracts/                  # Shared specs
    └── environments/          # Action/observation space definitions
```

## Key Concepts

### Environment Contracts

Located in `contracts/environments/`, these JSON files define:
- Observation space dimensions
- Action space (MultiDiscrete with dependencies)
- Action masking rules

Both `simulation-rsps` (Java) and `pvp-ml` (Python) read these contracts.

### Model Files

Trained models are saved as `.zip` files containing:
- Policy network weights
- Normalization statistics
- Training metadata

Production path: `pvp-ml/models/FineTunedNh.zip`

### Communication Protocols

| Protocol | Port | Format | Use Case |
|----------|------|--------|----------|
| HTTP | 8080 | JSON REST | Items, tasks, general API |
| TCP | 5555 | Newline-delimited JSON | ML inference (low latency) |
| TCP | 7070 | Newline-delimited JSON | Training env (RSPS ↔ pvp-ml) |

## Development Workflow

### Adding a New API Endpoint

1. Create router in `backend/src/osrs_backend/api/routers/`
2. Register in `backend/src/osrs_backend/api/app.py`
3. Add tests in `backend/tests/`

### Training a New Model

1. Create preset YAML in `pvp-ml/config/`
2. Run training: `train --preset config/your_preset.yml`
3. Evaluate: `eval --model experiments/YourExperiment/model.zip`
4. Deploy to `models/` directory

### Modifying Game Mechanics

1. Edit Java code in `simulation-rsps/ElvargServer/`
2. Rebuild: `./gradlew shadowJar`
3. Restart training server

## Environment Variables

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost` | Redis for background jobs |
| `MODEL_PATH` | `models/FineTunedNh.zip` | Default model to load |

### Training (pvp-ml)

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_DIR` | Auto-detected | Repository root for distributed training |
| `CUDA_VISIBLE_DEVICES` | - | GPU selection |

### Simulation (simulation-rsps)

| Variable | Default | Description |
|----------|---------|-------------|
| `TRAIN` | `false` | Enable RL training mode |
| `REMOTE_ENV_PORT` | `7070` | Socket API port |
| `SYNC_TRAINING` | `false` | Deterministic mode (1ms ticks) |

## CI/CD

Use path filters to build only what changed:

```yaml
# .github/workflows/backend.yml
on:
  push:
    paths: ['backend/**']

# .github/workflows/training.yml
on:
  push:
    paths: ['pvp-ml/**', 'simulation-rsps/**']
```

## Common Tasks

### Check if model server is running
```bash
curl http://localhost:8080/healthcheck
```

### Test TCP inference
```bash
echo '{"obs": [[0.5, 0.3, ...]], "actionMasks": [[true, true, ...]]}' | nc localhost 5555
```

### View training progress
```bash
tensorboard --logdir pvp-ml/tensorboard/
```

## Troubleshooting

### Port already in use
```bash
lsof -i :5555  # Find process using port
kill -9 <PID>
```

### Model not loading
- Check `MODEL_PATH` environment variable
- Verify model file exists and is valid zip
- Check PyTorch version compatibility

### Training not connecting to RSPS
- Ensure `TRAIN=true` is set on Java server
- Check `REMOTE_ENV_PORT` matches pvp-ml config
- Verify firewall allows localhost connections
