# Project Consolidation Strategy

## Overview

Consolidate 4 OSRS Dreambot projects into 2 repositories:
1. **Java Client Repo**: BotScript (base) + ripker functionality
2. **Python Server Repo**: BotCommand + bot_command

### Related Projects
- `/Users/scoutfullner/dev/ripker` - Dreambot PvP RL client (to merge into BotScript)
- `/Users/scoutfullner/dev/BotScript` - General Dreambot scripting client (base)
- `/Users/scoutfullner/dev/bot_command` - Python backend for Dreambot (to merge here)
- `/Users/scoutfullner/dev/BotCommand` - This repo (RL training + serving)

---

## Part 1: Java Client Consolidation (ripker → BotScript)

### Strategy

Adapt ripker's RL PvP functionality into BotScript's TreeScript behavior tree architecture. BotScript becomes the unified client.

### Target Package Structure

```
com.kroonjay/
├── api/
│   ├── context/
│   │   ├── UniversalContext.java         # Existing
│   │   └── PvpContext.java               # NEW - PvP/RL state
│   ├── events/
│   │   ├── EventBus.java                 # Existing
│   │   └── PvpEventHandlers.java         # NEW - Hitsplat/Animation/Tick
│   ├── tasks/
│   │   ├── TaskBuilder.java              # MODIFY - add PVP case
│   │   └── behaviors/
│   │       └── pvp/                      # NEW package
│   │           ├── PvpBehavior.java      # TaskBehavior implementation
│   │           ├── PvpBranch.java        # TreeScript branch
│   │           └── PvpLeaf.java          # Executes RL loop
│   ├── rl/                               # NEW - migrated from ripker
│   │   ├── client/
│   │   │   └── PvpClient.java            # TCP socket to ML server
│   │   └── environments/
│   │       ├── AgentEnvironment.java
│   │       └── nh/
│   │           ├── NhEnvironment.java    # Observation/action logic
│   │           └── NhLoadout.java
│   └── utils/
│       ├── timers/                       # NEW - migrated from ripker
│       │   ├── DreamBotTimerManager.java
│       │   └── TimerKey.java
│       └── enums/gear/                   # KEEP (single source of truth)
│           ├── Gear.java
│           ├── Weapon.java
│           └── ...
```

### Key Design Decisions

| Question | Decision |
|----------|----------|
| How does RL fit TreeScript? | Custom `PvpBranch` encapsulates entire RL loop |
| Leaf or Branch? | Branch with single Leaf for tick execution |
| 600ms tick timing? | `PvpLeaf.onLoop()` returns exactly 600 |
| Async actions? | Keep CompletableFuture pattern from ripker |

### Migration Phases

**Phase 1: Consolidate Shared Code**
- Delete ripker's gear enums (use BotScript's)
- Merge utility classes (GearUtils, CombatUtils)

**Phase 2: Migrate Timer System**
- Copy `ripker/timers/*` → `com.kroonjay.api.utils.timers`

**Phase 3: Migrate RL Infrastructure**
- Copy PvpClient, AgentEnvironment, NhEnvironment
- Update imports to use BotScript packages

**Phase 4: Create Behavior Tree Components**
- Implement PvpBehavior, PvpBranch, PvpLeaf
- Add PVP to TaskType enum
- Update TaskBuilder to route PVP tasks

**Phase 5: Integrate Events**
- Create PvpEventHandlers for hitsplats, animations, game ticks
- Wire into BotScript's event system

### Files to Create
1. `com.kroonjay.api.context.PvpContext`
2. `com.kroonjay.api.tasks.behaviors.pvp.PvpBehavior`
3. `com.kroonjay.api.tasks.behaviors.pvp.PvpBranch`
4. `com.kroonjay.api.tasks.behaviors.pvp.PvpLeaf`
5. `com.kroonjay.api.events.PvpEventHandlers`

### Files to Migrate (from ripker)
- `PvpClient.java` → `com.kroonjay.api.rl.client`
- `environments/*` → `com.kroonjay.api.rl.environments`
- `timers/*` → `com.kroonjay.api.utils.timers`
- `PlayerActionMonitor.java` → `com.kroonjay.api.rl`

### Files to Delete (after migration)
- Entire `ripker/utils/enums/gear/` directory

---

## Part 2: Python Server Consolidation (pvp-ml + bot_command)

### Strategy

Single FastAPI application serving both HTTP (bot_command) and TCP (pvp-ml inference) protocols with shared infrastructure.

### Target Structure

```
BotCommand/
├── simulation-rsps/              # Unchanged (training only)
├── contracts/                    # Unchanged
├── models/                       # Trained model files
│
├── backend/                      # NEW unified server
│   ├── pyproject.toml
│   ├── src/osrs_backend/
│   │   ├── main.py               # Unified entry point
│   │   ├── config.py             # Shared configuration
│   │   │
│   │   ├── api/                  # HTTP layer (from bot_command)
│   │   │   ├── app.py
│   │   │   └── routers/
│   │   │       ├── items.py
│   │   │       ├── actions.py
│   │   │       ├── tasks.py
│   │   │       ├── healthcheck.py
│   │   │       └── ml.py         # NEW optional HTTP ML endpoint
│   │   │
│   │   ├── tcp/                  # TCP layer (from pvp-ml)
│   │   │   ├── server.py
│   │   │   └── protocol.py
│   │   │
│   │   ├── services/             # Shared business logic
│   │   │   ├── inference.py      # Model inference
│   │   │   ├── items.py
│   │   │   └── prices.py
│   │   │
│   │   ├── ml/                   # ML code (from pvp-ml)
│   │   │   ├── model_loader.py
│   │   │   └── remote_processor.py
│   │   │
│   │   ├── db/                   # Database (from bot_command)
│   │   │   ├── database.py
│   │   │   └── prisma/
│   │   │
│   │   └── workers/              # Background jobs
│   │       └── arq_worker.py
│   │
│   └── tests/
│
└── training/                     # Renamed from pvp-ml
    ├── train.py
    ├── evaluate.py
    ├── env/
    ├── ppo/
    └── callback/
```

### Key Design Decisions

| Question | Decision |
|----------|----------|
| One process or two? | Single process, both protocols via asyncio |
| Protocol handling? | Keep TCP for low-latency inference, HTTP for everything else |
| Database sharing? | Yes, single PostgreSQL with Prisma |
| Entry points? | Unified CLI: `osrs serve`, `osrs worker`, `osrs train` |

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Unified Backend Process                    │
├──────────────────────────────────────────────────────────────┤
│  FastAPI (HTTP :8080)          │  TCP Server (:9999)         │
│  ├─ /actions/*                 │  └─ Model inference         │
│  ├─ /items/*                   │                              │
│  ├─ /healthcheck/*             │                              │
│  └─ /ml/predict (optional)     │                              │
├──────────────────────────────────────────────────────────────┤
│              Shared Services Layer                            │
│  └─ InferenceService, ItemService, PriceService              │
├──────────────────────────────────────────────────────────────┤
│              Infrastructure                                   │
│  └─ PostgreSQL (Prisma), Redis (ARQ), Model Cache            │
└──────────────────────────────────────────────────────────────┘
```

### How FastAPI + TCP Coexist

The FastAPI lifespan hook starts the TCP server alongside HTTP:

```python
# backend/src/osrs_backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: start TCP server in background
    tcp_server = await asyncio.start_server(
        handle_inference_client,
        host="0.0.0.0",
        port=9999
    )

    yield  # FastAPI runs here

    # Shutdown: close TCP server
    tcp_server.close()
    await tcp_server.wait_closed()

app = FastAPI(lifespan=lifespan)
```

### Why Keep Both Protocols?

| Protocol | Use Case | Latency | Client |
|----------|----------|---------|--------|
| HTTP (FastAPI) | Items, actions, healthcheck | ~5-15ms | BotScript |
| TCP Socket | Model inference (predict action) | ~1-3ms | ripker/RL client |

For PvP combat at 600ms ticks, the ~5-10ms saved by TCP matters.

### Unified CLI

```bash
osrs serve              # Start HTTP + TCP server
osrs serve --http-only  # HTTP only (port 8080)
osrs serve --tcp-only   # TCP only (port 9999)
osrs worker             # Start ARQ background worker
osrs train --preset ... # Delegate to training module
osrs eval --model ...   # Delegate to training module
```

---

## Decisions Made

- **Client location**: Expand BotScript repo in place (preserve git history)
- **Training code**: Separate `training/` directory (not installed with server)
- **Order**: Server first, then client

---

## Implementation Order

### Phase 1: Server Consolidation (Do First)

**Step 1.1: Create backend structure**
```bash
cd /Users/scoutfullner/dev/BotCommand
mkdir -p backend/src/osrs_backend/{api/routers,tcp,services,ml,db,workers}
```

**Step 1.2: Migrate bot_command**
- Copy `bot_command/api/routers/*` → `backend/src/osrs_backend/api/routers/`
- Copy `bot_command/models/*` → `backend/src/osrs_backend/models/`
- Copy `bot_command/db/*` → `backend/src/osrs_backend/db/`
- Copy `bot_command/workers/*` → `backend/src/osrs_backend/workers/`
- Copy `bot_command/tasks/*` → `backend/src/osrs_backend/tasks/`
- Adapt imports to new package structure

**Step 1.3: Migrate pvp-ml inference**
- Extract TCP server from `pvp-ml/pvp_ml/api.py` → `backend/src/osrs_backend/tcp/server.py`
- Create `backend/src/osrs_backend/services/inference.py`
- Copy model loading from `pvp-ml/pvp_ml/util/remote_processor/`

**Step 1.4: Move training code**
- Rename `pvp-ml/` → `training/`
- Remove api.py (now in backend)
- Keep train.py, evaluate.py, env/, ppo/, callback/

**Step 1.5: Create unified entry point**
- Create `backend/src/osrs_backend/main.py`
- Create `backend/src/osrs_backend/cli.py` with click
- Add pyproject.toml with entry points

**Step 1.6: Test server**
- Verify HTTP endpoints work (items, actions, healthcheck)
- Verify TCP inference works
- Verify background workers run

### Phase 2: Client Consolidation

**Step 2.1: Add packages to BotScript**
```bash
cd /Users/scoutfullner/dev/BotScript
mkdir -p src/main/java/com/kroonjay/api/rl/{client,environments/nh}
mkdir -p src/main/java/com/kroonjay/api/utils/timers
mkdir -p src/main/java/com/kroonjay/api/tasks/behaviors/pvp
```

**Step 2.2: Migrate timer system**
- Copy `ripker/timers/*` → `com.kroonjay.api.utils.timers`
- Update package declarations and imports

**Step 2.3: Migrate RL infrastructure**
- Copy `PvpClient.java` → `com.kroonjay.api.rl.client`
- Copy `environments/*` → `com.kroonjay.api.rl.environments`
- Copy `PlayerActionMonitor.java` → `com.kroonjay.api.rl`
- Update imports to use existing gear enums

**Step 2.4: Create behavior tree components**
- Create `PvpContext.java`
- Create `PvpBehavior.java` (implements TaskBehavior)
- Create `PvpBranch.java` (extends Branch)
- Create `PvpLeaf.java` (extends Leaf)
- Add `PVP` to TaskType enum
- Update TaskBuilder with PVP case

**Step 2.5: Integrate events**
- Create `PvpEventHandlers.java`
- Wire into EventBus

**Step 2.6: Test client**
- Build: `mvn clean package`
- Test RL PvP connects to server
- Test existing BotScript behaviors still work

### Phase 3: Cleanup

**Step 3.1: Archive old repos**
- Archive ripker repo (functionality now in BotScript)
- Archive bot_command repo (functionality now in backend)

**Step 3.2: Update documentation**
- Update CLAUDE.md with new structure
- Document unified CLI commands
- Document new TaskType for PVP

---

## Verification

### Server Tests
- HTTP: `curl http://localhost:8080/items/`
- TCP: Existing pvp-ml integration test
- Background: Price fetching runs on schedule

### Client Tests
- Build: `mvn clean package` produces single JAR
- RL PvP: Connect to server, run combat loop
- General tasks: Existing BotScript functionality works

---

## Critical Files

### Java (to modify/create)
- `/Users/scoutfullner/dev/BotScript/src/main/java/com/kroonjay/api/tasks/TaskBuilder.java`
- `/Users/scoutfullner/dev/ripker/src/main/java/ripker/environments/nh/NhEnvironment.java`
- `/Users/scoutfullner/dev/ripker/src/main/java/ripker/PvpClient.java`

### Python (to migrate/merge)
- `/Users/scoutfullner/dev/BotCommand/pvp-ml/pvp_ml/api.py`
- `/Users/scoutfullner/dev/bot_command/api/api.py`
- `/Users/scoutfullner/dev/bot_command/db/database.py`
