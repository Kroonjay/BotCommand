# CLAUDE.md - Project Guide

## Project Overview

This repository implements a reinforcement learning system for Old School RuneScape PvP combat. It consists of two integrated components:

1. **simulation-rsps/** - A Java-based private RuneScape server (Elvarg) modified with an RL plugin that exposes game environments via a socket API
2. **pvp-ml/** - A Python ML framework using PPO with self-play strategies to train combat agents

The trained models achieve ~99% win rate against human players in OSRS LMS/PvP Arena.

## Architecture

```
┌─────────────────────┐         JSON/Socket          ┌─────────────────────┐
│   simulation-rsps   │◄───────────────────────────►│      pvp-ml         │
│   (Java Server)     │        Port 7070            │   (Python ML)       │
│                     │                              │                     │
│  - Game mechanics   │  Actions: login, logout,     │  - PPO training     │
│  - Combat sim       │  reset, step, debug          │  - Self-play        │
│  - Env registry     │                              │  - Model serving    │
└─────────────────────┘                              └─────────────────────┘
```

## Quick Reference

### Build & Run Commands

**Java Server (simulation-rsps/ElvargServer/):**
```bash
# Build
./gradlew shadowJar

# Run with RL enabled
TRAIN=true REMOTE_ENV_PORT=7070 ./gradlew run

# Sync training mode (deterministic, 1 tick/sec)
TRAIN=true SYNC_TRAINING=true ./gradlew run
```

**Python ML (pvp-ml/):**
```bash
# Setup environment
conda env create -f environment.yml
conda activate osrs

# Install package
pip install -e .

# Train with preset config
train --preset config/nh/core.yml --experiment MyExperiment

# Full job (starts server + tensorboard + training)
python -m pvp_ml.run_train_job --preset config/nh/prioritized-past-self-play.yml

# Serve model API
serve-api --model models/FineTunedNh.zip --port 5555

# Evaluate model
eval --model models/FineTunedNh.zip
```

### Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRAIN` | false | Enable RL training mode |
| `REMOTE_ENV_PORT` | 7070 | Socket API port |
| `GAME_PORT` | 43594 | Game client port |
| `SYNC_TRAINING` | false | Synchronous training (tick=1ms) |

## Component Details

### simulation-rsps (Java)

**Main entry:** `com.elvarg.Server`

**RL Infrastructure (`com.github.naton1.rl/`):**
- `ReinforcementLearningPlugin.java` - Main plugin, registers on server start
- `RemoteEnvironmentServer.java` - Socket server handling API routes
- `EnvironmentRegistry.java` - Available environments (NH, DHAROK)
- `RemoteEnvironmentPlayerBot.java` - Agent-controlled player

**Environments (`com.github.naton1.rl.env/`):**
- `nh/NhEnvironment.java` - Primary No-Honor PvP environment (~11 action heads)
- `nh/NhBaseline.java` - Scripted baseline opponent
- `dharok/` - Dharok-specific test environment

**Key patterns:**
- Environments implement `Environment` interface
- Events dispatched via `EventDispatcher` singleton
- Plugins discovered via `PluginLoader` (checks for `Plugin` implementations)
- JSON protocol uses camelCase field names

### pvp-ml (Python)

**Entry points defined in setup.py:**
- `train` → `pvp_ml.run_train_job:main_entry_point`
- `serve-api` → `pvp_ml.api:main_entry_point`
- `eval` → `pvp_ml.evaluate:main_entry_point`

**Core modules:**

| Directory | Purpose |
|-----------|---------|
| `env/` | Gymnasium environments, RSPS connector |
| `ppo/` | PPO algorithm, policy networks, buffers |
| `callback/` | Training callbacks (checkpointing, eval, self-play) |
| `util/` | Helpers (schedules, ELO, league management) |
| `scripted/` | Scripted baseline agents |
| `config/` | YAML training presets |

**Important files:**
- `env/pvp_env.py` - Main `PvpEnv` Gymnasium wrapper
- `env/remote_env_connector.py` - AsyncIO socket client to RSPS
- `env/simulation.py` - RSPS process manager
- `train.py` - Training script (100+ CLI args, see TRAIN_OPTIONS.md)
- `api.py` - Model inference API server

### contracts/environments/

JSON specifications defining action/observation spaces:
- `NhEnv.json` - 11-head MultiDiscrete action space with dependencies
- `DharokEnv.json` - Test environment spec

## Communication Protocol

**Transport:** TCP sockets, newline-delimited JSON (ASCII)

**Request format:**
```json
{
  "action": "login|logout|reset|step|debug",
  "body": {...},
  "meta": {"id": "environment-id"}
}
```

**Response format:**
```json
{
  "error": false,
  "body": {...}
}
```

**API routes:**
- `login` - Register agent with environment
- `logout` - Disconnect agent
- `reset` - Reset fight, returns initial observation
- `step` - Execute action, returns obs/reward/done/info
- `debug` - Debug information

## Training Strategies

**Self-play variants (configured via presets):**
- **Pure self-play** - Current model vs itself
- **Past self-play** - Prioritized league of historical checkpoints
- **Target self-play** - Specific opponent models
- **Latest self-play** - Latest model from different experiment
- **Exploiter training** - Dedicated network finds weaknesses

**Reward shaping:**
- Configurable via `--reward-*` flags
- Schedules: constant, linear, exponential, step, expression
- Key rewards: damage dealt, health preserved, KO bonuses

## Key Files by Task

**Adding new environment:**
1. Create Java env in `simulation-rsps/.../rl/env/newenv/`
2. Register in `EnvironmentRegistry.java`
3. Create contract JSON in `contracts/environments/`
4. Add Python config preset in `pvp-ml/config/`

**Modifying combat mechanics:**
- `simulation-rsps/.../game/content/combat/` - Combat system
- `simulation-rsps/.../game/model/equipment/` - Equipment/weapons

**Adjusting reward shaping:**
- `pvp-ml/pvp_ml/env/pvp_env.py` - Reward calculation logic
- CLI flags in `train.py` or preset YAML files

**Adding training callbacks:**
- Implement in `pvp-ml/pvp_ml/callback/`
- Register in `train.py` callback list

## Models

**Pre-trained (pvp-ml/models/):**
- `FineTunedNh.zip` - Production model, ~99% win rate
- `GeneralizedNh.zip` - Base self-play trained model

**Reference checkpoints (pvp-ml/reference/):**
- Historical training checkpoints for past self-play

## Development Notes

- Python uses asyncio for non-blocking I/O to 100+ parallel RSPS connections
- Default training: 100 envs × 1024 rollout steps = 102,400 steps/rollout
- Java server tick rate: 600ms (normal), 1ms (sync training mode)
- Action masking enforces dependencies between action heads
- Models compatible with TorchScript for production serving

## Common Issues

**Port conflicts:** Training jobs use ports starting at 43595 (game) and 7070 (env). Check `train_jobs.json` for active jobs.

**Memory:** Java server needs 2-3GB heap. Set in Dockerfile or Gradle.

**CUDA:** PyTorch configured for CUDA 12.1. CPU training also supported.

## Testing

```bash
# Python integration test
cd pvp-ml && python test/integ/api_client.py

# Java builds include tests via Gradle
cd simulation-rsps/ElvargServer && ./gradlew test
```
