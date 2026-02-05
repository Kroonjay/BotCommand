# Simulation RSPS - Training Environment

## Overview

A modified Elvarg RuneScape private server used **only for training** RL agents. Not used in production.

## Quick Start

```bash
cd ElvargServer

# Build
./gradlew shadowJar

# Run with RL enabled
TRAIN=true REMOTE_ENV_PORT=7070 ./gradlew run

# Sync training mode (deterministic, faster)
TRAIN=true SYNC_TRAINING=true ./gradlew run
```

## Architecture

```
pvp-ml (Python)                    simulation-rsps (Java)
┌─────────────┐                    ┌─────────────────────┐
│  Training   │◄──── Socket ──────►│  Elvarg Server      │
│  Loop       │      Port 7070     │                     │
│             │                    │  ┌───────────────┐  │
│  - reset()  │  ───────────────►  │  │ RL Plugin     │  │
│  - step()   │  ◄───────────────  │  │ - Environments│  │
│  - login()  │                    │  │ - Bot Players │  │
│             │                    │  └───────────────┘  │
└─────────────┘                    └─────────────────────┘
```

## Key Directories

```
ElvargServer/src/main/java/
├── com/elvarg/                    # Base server
│   ├── Server.java                # Entry point
│   └── game/
│       ├── content/combat/        # Combat mechanics
│       ├── model/equipment/       # Weapons, armor
│       └── entity/impl/player/    # Player logic
│
└── com/github/naton1/rl/         # RL Plugin
    ├── ReinforcementLearningPlugin.java  # Main plugin
    ├── RemoteEnvironmentServer.java      # Socket API
    ├── EnvironmentRegistry.java          # Env registration
    ├── AgentPlayerBot.java               # Bot-controlled player
    │
    └── env/                       # Environments
        ├── Environment.java       # Interface
        ├── nh/                    # No-Honor PvP
        │   ├── NhEnvironment.java
        │   └── NhBaseline.java   # Scripted opponent
        └── dharok/               # Dharok test env
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRAIN` | `false` | Enable RL mode |
| `REMOTE_ENV_PORT` | `7070` | Socket API port |
| `GAME_PORT` | `43594` | Game client port |
| `SYNC_TRAINING` | `false` | 1ms ticks (faster training) |

## Socket Protocol

Port 7070, newline-delimited JSON:

```json
// Request
{"action": "login|logout|reset|step|debug", "body": {...}, "meta": {"id": "env-id"}}

// Response
{"error": false, "body": {...}}
```

### Actions

| Action | Description |
|--------|-------------|
| `login` | Register agent with environment |
| `logout` | Disconnect agent |
| `reset` | Reset fight, get initial observation |
| `step` | Execute action, get obs/reward/done |
| `debug` | Debug information |

## Adding a New Environment

1. Create package in `env/`:
```java
package com.github.naton1.rl.env.myenv;

public class MyEnvironment implements Environment {
    @Override
    public Observation reset() { ... }

    @Override
    public StepResult step(Action action) { ... }
}
```

2. Register in `EnvironmentRegistry.java`:
```java
registry.register("myenv", MyEnvironment::new);
```

3. Create contract in `contracts/environments/MyEnv.json`

## Modifying Combat Mechanics

Combat code is in `com/elvarg/game/content/combat/`:

- `CombatFactory.java` - Combat initialization
- `CombatFormulae.java` - Damage/accuracy calculations
- `hit/` - Hit processing
- `method/` - Attack methods (melee, ranged, magic)

## Testing

```bash
./gradlew test
```

## Notes

- Server tick rate: 600ms (normal), 1ms (SYNC_TRAINING=true)
- Memory: Needs 2-3GB heap for many parallel environments
- This server is NOT connected to real OSRS - it's a simulation
