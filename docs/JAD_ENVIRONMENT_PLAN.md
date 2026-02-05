# TzTok-Jad PvM Training Environment - Implementation Plan

## Overview

Create a **reusable PvM training framework** with TzTok-Jad as the first implementation. The architecture will be modular to support future bosses (Zulrah, Vorkath, etc.) without modifying existing PvP code.

## Design Principles

1. **No modifications to existing PvP code** - All PvM code is additive
2. **Reusable Python framework** - `pvm_env.py` base class for all PvM scenarios
3. **Boss-specific extensions** - Java environments and Python configs per boss
4. **Shared infrastructure** - Leverage existing socket protocol, training pipeline

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Python Side                              │
├─────────────────────────────────────────────────────────────────┤
│  pvp_env.py (existing, unchanged)                                │
│                                                                  │
│  pvm_env.py (NEW - base class)                                   │
│    ├── PvmEnv(gymnasium.Env)                                     │
│    │     ├── Common PvM observations (player state, boss HP)     │
│    │     ├── Common reward signals (kill, death, damage)         │
│    │     └── Boss-agnostic action processing                     │
│    │                                                             │
│    └── Subclasses per boss:                                      │
│          ├── JadEnv(PvmEnv) - Prayer switching rewards           │
│          ├── ZulrahEnv(PvmEnv) - Phase/rotation rewards (future) │
│          └── VorkathEnv(PvmEnv) - Woox walk rewards (future)     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Java Side                               │
├─────────────────────────────────────────────────────────────────┤
│  Existing (unchanged):                                           │
│    ├── AgentEnvironment interface                                │
│    ├── EnvironmentRegistry                                       │
│    ├── RemoteEnvironmentServer                                   │
│    └── nh/, dharok/ packages                                     │
│                                                                  │
│  New PvM package:                                                │
│    └── pvm/                                                      │
│          ├── PvmEnvironment.java (base class for PvM envs)       │
│          ├── PvmEnvironmentDescriptor.java                       │
│          └── jad/                                                │
│                ├── JadEnvironment.java                           │
│                ├── JadEnvironmentParams.java                     │
│                └── JadLoadout.java + variants                    │
└─────────────────────────────────────────────────────────────────┘
```

## Files to Create

### Python (pvp-ml/pvp_ml/env/)

| File | Purpose |
|------|---------|
| `pvm_env.py` | **Base PvM environment class** - common obs/rewards/actions for all PvM |
| `jad_env.py` | **Jad-specific extensions** - prayer rewards, healer tracking |

### Java (simulation-rsps/.../com/github/naton1/rl/env/pvm/)

| File | Purpose |
|------|---------|
| `PvmEnvironment.java` | Base class with common NPC combat handling |
| `PvmEnvironmentDescriptor.java` | Base descriptor for PvM environments |
| `jad/JadEnvironment.java` | Jad-specific environment logic |
| `jad/JadEnvironmentDescriptor.java` | Jad factory |
| `jad/JadEnvironmentParams.java` | Jad config (healers, build type) |
| `jad/JadLoadout.java` | Interface for Jad loadouts |
| `jad/JadMaxedLoadout.java` | Maxed account loadout |
| `jad/JadMedLoadout.java` | Med-level loadout |
| `jad/JadPureLoadout.java` | Pure loadout |
| `jad/JadArea.java` | Private fight area |

### Contract

| File | Purpose |
|------|---------|
| `contracts/environments/JadEnv.json` | Action/observation space for Jad |

### Config

| File | Purpose |
|------|---------|
| `pvp-ml/config/jad/core.yml` | Base Jad training config |
| `pvp-ml/config/jad/curriculum.yml` | Phased training (optional) |

## Python PvM Framework Design

### pvm_env.py - Base Class

```python
class PvmEnv(gymnasium.Env):
    """Base environment for all PvM (Player vs Monster) scenarios."""

    def __init__(
        self,
        env_name: str,                    # e.g., "JadEnv"
        connector: RemoteEnvConnector,
        # Common PvM rewards (can be overridden per boss)
        win_reward: Schedule = ConstantSchedule(10.0),
        lose_reward: Schedule = ConstantSchedule(-10.0),
        timeout_reward: Schedule = ConstantSchedule(-5.0),
        damage_dealt_reward_scale: Schedule = ConstantSchedule(0.1),
        damage_received_reward_scale: Schedule = ConstantSchedule(-0.1),
        per_tick_reward: Schedule = ConstantSchedule(-0.001),
        # Common settings
        frame_stack: list[int] = None,
        normalize_observations: bool = True,
        **kwargs
    ):
        self.env_name = env_name
        self.connector = connector
        # ... store rewards and settings

    def _compute_base_reward(self, response: dict) -> float:
        """Common reward calculation for all PvM scenarios."""
        reward = 0.0
        meta = response.get("meta", {})

        # Terminal rewards
        terminal = response.get("terminalState")
        if terminal == "WON":
            reward += self.win_reward.value(self.total_timesteps)
        elif terminal == "LOST":
            reward += self.lose_reward.value(self.total_timesteps)
        elif terminal == "TIMEOUT":
            reward += self.timeout_reward.value(self.total_timesteps)

        # Damage rewards
        reward += meta.get("damageDealt", 0) * self.damage_dealt_reward_scale.value(...)
        reward += meta.get("damageReceived", 0) * self.damage_received_reward_scale.value(...)

        # Per-tick penalty
        reward += self.per_tick_reward.value(self.total_timesteps)

        return reward

    def _compute_boss_specific_reward(self, response: dict) -> float:
        """Override in subclasses for boss-specific rewards."""
        return 0.0

    def step(self, action):
        response = await self.connector.step(action)
        reward = self._compute_base_reward(response) + self._compute_boss_specific_reward(response)
        # ... rest of step logic
```

### jad_env.py - Jad-Specific

```python
class JadEnv(PvmEnv):
    """TzTok-Jad environment with prayer switching and healer management."""

    def __init__(
        self,
        connector: RemoteEnvConnector,
        # Jad-specific rewards
        correct_prayer_reward: Schedule = ConstantSchedule(0.5),
        wrong_prayer_reward: Schedule = ConstantSchedule(-3.0),
        no_prayer_penalty: Schedule = ConstantSchedule(-0.5),
        healer_tag_reward: Schedule = ConstantSchedule(0.3),
        jad_healed_penalty_scale: Schedule = ConstantSchedule(-0.1),
        all_healers_tagged_bonus: Schedule = ConstantSchedule(0.5),
        **kwargs
    ):
        super().__init__(env_name="JadEnv", connector=connector, **kwargs)
        # Store Jad-specific rewards

    def _compute_boss_specific_reward(self, response: dict) -> float:
        """Jad-specific reward signals."""
        reward = 0.0
        meta = response.get("meta", {})

        # Prayer switching rewards (core mechanic)
        if meta.get("jadAttackLanded"):
            if meta.get("prayedCorrectly"):
                reward += self.correct_prayer_reward.value(...)
            else:
                reward += self.wrong_prayer_reward.value(...)

        if not meta.get("anyPrayerActive"):
            reward += self.no_prayer_penalty.value(...)

        # Healer management
        if meta.get("healerTaggedThisTick"):
            reward += self.healer_tag_reward.value(...)

        reward += meta.get("jadHealedAmount", 0) * self.jad_healed_penalty_scale.value(...)

        if meta.get("allHealersTagged") and not self._all_healers_bonus_given:
            reward += self.all_healers_tagged_bonus.value(...)
            self._all_healers_bonus_given = True

        return reward
```

## Java PvM Framework Design

### PvmEnvironment.java - Base Class

```java
public abstract class PvmEnvironment implements AgentEnvironment {

    protected final Player agent;
    protected final NPC boss;  // Generic NPC instead of Player target
    protected final EnvironmentCallback callback;

    // Common PvM tracking
    protected int totalDamageDealt;
    protected int totalDamageReceived;
    protected int episodeTicks;

    @Override
    public Player getAgent() { return agent; }

    @Override
    public Player getTarget() { return null; }  // No player target in PvM

    public NPC getBoss() { return boss; }

    // Common observations for all PvM
    protected List<Number> getCommonObs() {
        return List.of(
            getPlayerHealthPercent(),
            getPlayerPrayerPercent(),
            getBossHealthPercent(),
            getDistanceToBoss(),
            // ... common stats
        );
    }

    // Subclasses add boss-specific observations
    protected abstract List<Number> getBossSpecificObs();

    @Override
    public List<Number> getObs() {
        List<Number> obs = new ArrayList<>(getCommonObs());
        obs.addAll(getBossSpecificObs());
        return obs;
    }

    // Common action processing
    protected void processCommonActions(List<Integer> action) {
        handleFood(action.get(FOOD_INDEX));
        handlePotion(action.get(POTION_INDEX));
        handleAttack(action.get(ATTACK_INDEX));
    }

    // Subclasses add boss-specific actions
    protected abstract void processBossSpecificActions(List<Integer> action);
}
```

### JadEnvironment.java - Extends PvmEnvironment

```java
public class JadEnvironment extends PvmEnvironment {

    private final TztokJad jad;
    private final List<YtHurKot> healers = new ArrayList<>();

    // Jad-specific state
    private CombatType jadPendingAttackType;
    private int ticksUntilDamage;
    private boolean healersSpawned;
    private boolean prayedCorrectlyThisTick;

    @Override
    protected List<Number> getBossSpecificObs() {
        return List.of(
            // Prayer state
            isProtectMeleeActive() ? 1 : 0,
            isProtectRangedActive() ? 1 : 0,
            isProtectMagicActive() ? 1 : 0,
            // Jad attack telegraph (CRITICAL)
            getJadPendingAttackType(),  // 0=none, 1=melee, 2=ranged, 3=magic
            ticksUntilDamage,
            // Healer state
            healersSpawned ? 1 : 0,
            getHealersAliveCount(),
            getHealersAggroCount(),
            getNearestUntaggedHealerDistance(),
            isJadBeingHealed() ? 1 : 0,
            // Per-healer tracking
            isHealer1Tagged(), isHealer2Tagged(),
            isHealer3Tagged(), isHealer4Tagged()
        );
    }

    @Override
    protected void processBossSpecificActions(List<Integer> action) {
        handlePrayer(action.get(PRAYER_INDEX));
        handleTargetSwitch(action.get(TARGET_INDEX));
        handleMovement(action.get(MOVEMENT_INDEX));
    }

    @Override
    public void onHitCalculated(PendingHit hit) {
        if (hit.getAttacker() == jad && hit.getTarget() == agent) {
            prayedCorrectlyThisTick = isPrayingCorrectlyFor(hit.getCombatType());
        }
    }
}
```

## Observation Space (~35 features)

### Common PvM Observations (in PvmEnvironment)
| Feature | Partial | Description |
|---------|---------|-------------|
| `player_health_percent` | yes | Current HP % |
| `player_prayer_percent` | yes | Prayer points % |
| `boss_health_percent` | no | Boss HP % |
| `boss_distance` | no | Distance to boss |
| `food_count` | yes | Food remaining |
| `special_energy` | no | Spec attack % |
| `player_attack_cooldown` | yes | Attack timing |
| `food_cooldown` | yes | Eat timing |
| `potion_cooldown` | no | Drink timing |

### Jad-Specific Observations (in JadEnvironment)
| Feature | Description |
|---------|-------------|
| `protect_melee_active` | Melee prayer on |
| `protect_ranged_active` | Ranged prayer on |
| `protect_magic_active` | Magic prayer on |
| `jad_attack_type_pending` | 0=none, 1=melee, 2=ranged, 3=magic |
| `ticks_until_damage` | Countdown to damage |
| `healers_spawned` | Whether healers active |
| `healers_alive_count` | Living healers (0-4) |
| `healers_aggro_count` | Healers on player |
| `nearest_healer_distance` | Distance to untagged healer |
| `jad_being_healed` | Jad receiving heals |
| `healer_1-4_tagged` | Per-healer aggro state |

## Action Space (7 heads)

| Head | Options | Description |
|------|---------|-------------|
| `prayer` | 4 | no-change, protect-magic, protect-ranged, protect-melee |
| `target` | 3 | no-change, target-boss, target-nearest-healer |
| `attack` | 3 | no-attack, basic-attack, special-attack |
| `food` | 2 | don't-eat, eat-food |
| `karambwan` | 2 | don't-eat, eat-karambwan |
| `potion` | 5 | none, brew, restore, ranging, combat |
| `movement` | 5 | stay, move-closer, move-away, move-left, move-right |

## Reward Design

### Base PvM Rewards (in pvm_env.py)
| Signal | Weight | Description |
|--------|--------|-------------|
| Kill boss | +10.0 | Episode win |
| Player death | -10.0 | Episode loss |
| Timeout | -5.0 | Took too long |
| Damage to boss | +0.1 scaled | DPS incentive |
| Damage received | -0.1 scaled | Survival incentive |
| Per tick | -0.001 | Efficiency incentive |

### Jad-Specific Rewards (in jad_env.py)
| Signal | Weight | Description |
|--------|--------|-------------|
| Correct prayer | +0.5 | Per successful switch |
| Wrong prayer | -3.0 | Core mechanic penalty |
| No prayer active | -0.5 | Per tick unprotected |
| Tag healer | +0.3 | Per healer aggro'd |
| Jad healed | -0.1 scaled | Per HP restored |
| All healers tagged | +0.5 | One-time bonus |

## Implementation Order

### Phase 1: Python Framework (Day 1)
1. Create `pvp-ml/pvp_ml/env/pvm_env.py` base class
2. Create `pvp-ml/pvp_ml/env/jad_env.py` Jad implementation
3. Update `pvp-ml/pvp_ml/env/__init__.py` exports

### Phase 2: Java Framework (Day 2)
4. Create `pvm/` package in `simulation-rsps/.../rl/env/`
5. Create `PvmEnvironment.java` base class
6. Create `PvmEnvironmentDescriptor.java`

### Phase 3: Jad Java Implementation (Day 3-4)
7. Create `pvm/jad/` package
8. `JadEnvironmentParams.java`
9. `JadLoadout.java` interface + `JadMaxedLoadout.java`
10. `JadArea.java` - private area with healer spawn logic
11. `JadEnvironment.java` - full implementation
12. `JadEnvironmentDescriptor.java`

### Phase 4: Registration & Config (Day 5)
13. Add `JAD("JadEnv", new JadEnvironmentDescriptor())` to `EnvironmentRegistry.java`
14. Create `contracts/environments/JadEnv.json`
15. Create `pvp-ml/config/jad/core.yml`

### Phase 5: Additional Loadouts & Testing (Day 6)
16. `JadMedLoadout.java`, `JadPureLoadout.java`
17. Integration testing
18. Reward tuning

## Key Files Summary

### New Files (no existing code modified except EnvironmentRegistry)

**Python:**
- `pvp-ml/pvp_ml/env/pvm_env.py` - Base PvM environment
- `pvp-ml/pvp_ml/env/jad_env.py` - Jad-specific environment

**Java:**
- `simulation-rsps/.../rl/env/pvm/PvmEnvironment.java`
- `simulation-rsps/.../rl/env/pvm/PvmEnvironmentDescriptor.java`
- `simulation-rsps/.../rl/env/pvm/jad/*.java` (7 files)

**Config:**
- `contracts/environments/JadEnv.json`
- `pvp-ml/config/jad/core.yml`

### Minimal Modification
- `EnvironmentRegistry.java` - Add single line: `JAD("JadEnv", new JadEnvironmentDescriptor())`

## Future Extensibility

With this framework, adding new bosses requires only:

1. **Java**: New `pvm/bossname/` package extending `PvmEnvironment`
2. **Python**: New `bossname_env.py` extending `PvmEnv`
3. **Contract**: New `contracts/environments/BossEnv.json`
4. **Config**: New `config/bossname/core.yml`
5. **Registry**: Add enum entry to `EnvironmentRegistry`

Example future bosses:
- **Zulrah**: Phase tracking, rotation rewards, position optimization
- **Vorkath**: Woox walk rewards, acid phase handling
- **Inferno**: Multi-wave tracking, Zuk mechanics

## Verification Plan

1. **Unit Test**: `PvmEnv` base class with mock connector
2. **Integration Test**: `JadEnv` with real Java server connection
3. **Prayer Test**: Verify correct/wrong prayer detection accuracy
4. **Healer Test**: Verify healer spawn and aggro tracking
5. **Reward Test**: Log all reward signals during manual play
6. **Training Test**: Short training run to verify learning signal
7. **Full Training**: Train to convergence, evaluate kill success rate

## Jad Attack Mechanics Reference

From `JadCombatMethod.java`:
```java
// Animation IDs
MELEE_ATTACK_ANIM = 2655  // 1-tick delay
RANGED_ATTACK_ANIM = 2652 // 3-tick delay, graphic 451
MAGIC_ATTACK_ANIM = 2656  // 3-tick delay, projectile 448

// Attack selection (in start method)
combatType = Misc.getRandom(1) == 0 ? RANGED : MAGIC;
if (distance <= 1 && Misc.getRandom(1) == 0) {
    combatType = MELEE;
}
```
