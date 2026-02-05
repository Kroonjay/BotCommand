# PvP-ML - Reinforcement Learning Training

## Overview

PPO-based RL training framework for OSRS PvP combat agents. Trains against the simulation-rsps server.

## Quick Start

```bash
# Setup
conda env create -f environment.yml
conda activate osrs
pip install -e .

# Train
train --preset config/nh/core.yml --experiment MyExperiment

# Full job (starts server + tensorboard + training)
python -m pvp_ml.run_train_job --preset config/nh/prioritized-past-self-play.yml

# Evaluate
eval --model models/FineTunedNh.zip

# Serve for inference
serve-api --model models/FineTunedNh.zip --port 5555
```

## Structure

```
pvp_ml/
├── train.py                # Training script (100+ CLI args)
├── evaluate.py             # Model evaluation
├── api.py                  # Inference server
├── run_train_job.py        # Full training orchestration
│
├── env/                    # Gymnasium environments
│   ├── pvp_env.py          # Main PvpEnv wrapper
│   ├── remote_env_connector.py  # AsyncIO socket client
│   └── simulation.py       # RSPS process manager
│
├── ppo/                    # PPO algorithm
│   ├── ppo.py              # Core algorithm
│   ├── policy.py           # Neural network policies
│   ├── buffer.py           # Rollout buffer
│   └── distributed/        # Ray distributed training
│
├── callback/               # Training callbacks
│   ├── checkpoint.py       # Model saving
│   ├── eval.py             # Periodic evaluation
│   ├── self_play.py        # Self-play opponent management
│   └── tensorboard.py      # Metrics logging
│
├── config/                 # Training presets
│   └── nh/
│       ├── core.yml        # Base config
│       └── prioritized-past-self-play.yml
│
├── scripted/               # Baseline agents
│   └── nh_baseline.py
│
└── util/                   # Utilities
    ├── schedules.py        # Learning rate schedules
    ├── elo.py              # ELO rating
    └── league.py           # Past-self league management

models/                     # Trained models
├── FineTunedNh.zip         # Production model
└── GeneralizedNh.zip       # Base model

experiments/                # Training run outputs
└── MyExperiment/
    ├── model.zip
    ├── config.yml
    └── logs/
```

## Training Presets

Presets in `config/` define training hyperparameters:

```yaml
# config/nh/core.yml
env:
  name: NhEnv
  num_envs: 100

ppo:
  learning_rate: 3e-4
  n_steps: 1024
  batch_size: 64
  n_epochs: 10

self_play:
  strategy: past  # pure, past, target, latest
  league_size: 20
```

## Self-Play Strategies

| Strategy | Description |
|----------|-------------|
| `pure` | Current model vs itself |
| `past` | Prioritized league of checkpoints |
| `target` | Specific opponent models |
| `latest` | Latest from different experiment |
| `exploiter` | Dedicated network finds weaknesses |

## Key CLI Args

See `TRAIN_OPTIONS.md` for full list. Common ones:

```bash
train \
  --preset config/nh/core.yml \
  --experiment MyExp \
  --total-timesteps 10000000 \
  --num-envs 100 \
  --learning-rate 3e-4 \
  --reward-damage-dealt 0.1 \
  --reward-ko 1.0
```

## Reward Shaping

Configured via `--reward-*` flags:

| Flag | Description |
|------|-------------|
| `--reward-damage-dealt` | Reward per damage point |
| `--reward-damage-received` | Penalty per damage taken |
| `--reward-ko` | Bonus for killing opponent |
| `--reward-death` | Penalty for dying |
| `--reward-health-preserved` | Bonus for remaining HP |

## Model Files

Models are saved as `.zip` containing:
- `policy.pth` - Network weights
- `obs_rms.pkl` - Observation normalization
- `metadata.json` - Training config

## Inference API

TCP server for BotScript integration:

```bash
serve-api --model models/FineTunedNh.zip --port 5555
```

Protocol:
```json
// Request
{"obs": [[...]], "actionMasks": [[...]], "deterministic": true}

// Response
{"action": [1, 0, 3, ...]}
```

## Distributed Training

Uses Ray for multi-machine training:

```bash
# Start Ray cluster
ray up cluster.yml

# Run distributed training
python -m pvp_ml.train --distributed --ray-address auto
```

## Monitoring

```bash
# TensorBoard
tensorboard --logdir tensorboard/

# View metrics
# - episode_reward
# - episode_length
# - policy_loss
# - value_loss
# - entropy
```

## Common Issues

### RSPS not connecting
- Ensure `TRAIN=true` on Java server
- Check port 7070 is available

### OOM during training
- Reduce `--num-envs`
- Reduce `--n-steps`

### Training not converging
- Check reward scale (should be ~0-10 range)
- Increase `--total-timesteps`
- Try different self-play strategy
