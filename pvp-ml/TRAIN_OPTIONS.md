# PvP ML Training Options

This document describes all available command-line options for the `train.py` script.

## Table of Contents
- [Basic Configuration](#basic-configuration)
- [Environment Settings](#environment-settings)
- [Self-Play Configuration](#self-play-configuration)
- [Training Parameters (PPO)](#training-parameters-ppo)
- [Network Architecture](#network-architecture)
- [Reward Shaping](#reward-shaping)
- [Evaluation & Testing](#evaluation--testing)
- [Distributed Training](#distributed-training)
- [Advanced Options](#advanced-options)

---

## Basic Configuration

### `--experiment-name`
- **Type**: String
- **Default**: `"test-experiment"`
- **Description**: Name of the experiment. Used for saving models, logs, and metrics.

### `--experiment-description`
- **Type**: String
- **Default**: `""`
- **Description**: Experiment description saved in meta file for future reference.

### `--env-name`
- **Type**: String
- **Default**: `"NhEnv"`
- **Choices**: Environment types defined in contracts (e.g., `NhEnv`, `DharokEnv`)
- **Description**: The PvP environment type to train on.

### `--load-file`
- **Type**: String
- **Default**: `""`
- **Description**: Path to a saved model file to load and continue training from.

### `--continue-training`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Helper argument to automatically load and continue training the latest model for the given experiment.

### `--allow-cleanup`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Allow cleaning up previous experiment data. Failsafe to prevent accidental deletion. Automatically enabled for test experiments.

### `--train-rollouts`
- **Type**: Integer
- **Default**: `None`
- **Description**: Number of rollouts to train for. If `None`, trains forever until manually stopped.

---

## Environment Settings

### `--num-envs`
- **Type**: Schedule
- **Default**: `ConstantSchedule(10)`
- **Description**: Number of parallel training environments to run.

### `--num-rollout-steps`
- **Type**: Schedule
- **Default**: `ConstantSchedule(256)`
- **Description**: Number of steps to sample for each environment per rollout.

### `--stack-frames`
- **Type**: Integer or List of Integers
- **Default**: `1`
- **Description**: Number of frames to stack, or frame indexes to stack (if a list). Index 0 is current frame, 1 is last frame, etc.

### `--remote-env-host`
- **Type**: String
- **Default**: `"localhost"`
- **Description**: Remote environment host for the simulation server to train on.

### `--remote-env-port`
- **Type**: Integer
- **Default**: `7070`
- **Description**: Remote environment port for the simulation server to train on.

### `--env-kwargs`
- **Type**: JSON Dictionary
- **Default**: `{}`
- **Description**: Additional keyword arguments to pass when initializing the environments.

### `--death-match`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Death match mode flag.

---

## Self-Play Configuration

### Pure Self-Play

#### `--self-play-percent`
- **Type**: Schedule
- **Default**: `ConstantSchedule(1.0)`
- **Description**: Percentage of environments that play against themselves (current model vs current model).

### Past Self-Play (Playing Against Historical Versions)

#### `--past-self-play-percent`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Percentage of environments that play against past versions of the model.

#### `--past-self-play-experiment`
- **Type**: String
- **Default**: Current experiment name
- **Description**: Name of experiment to load past models from. Defaults to current experiment.

#### `--past-self-play-deterministic-percent`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Percentage of past self-play environments that use deterministic (greedy) actions.

#### `--past-self-play-learning-rate`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.01)`
- **Description**: Learning rate for updating past self-play opponent models.

#### `--past-self-play-delay-chance`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Probability of adding input delay to past self agents.

#### `--add-past-self-play-league-targets`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Add new model checkpoints to the past self-play league rotation.

#### `--past-self-override-env-kwargs`
- **Type**: JSON Dictionary
- **Default**: `{}`
- **Description**: Environment kwargs overrides specifically for past self-play agents.

### Target Self-Play (Playing Against Specific Models)

#### `--target-self-play-percent`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Percentage of environments that play against specific target models.

#### `--target`
- **Type**: String (can be specified multiple times)
- **Default**: `[]`
- **Description**: Specific model paths to use as opponents (randomly selected from list). Use multiple times to add multiple targets.

#### `--target-self-play-deterministic-percent`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Percentage of target self-play that uses deterministic actions.

### Latest Self-Play (Playing Against Latest Model of Another Experiment)

#### `--latest-self-play-percent`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Percentage of environments that play against the latest model of another experiment.

#### `--latest-self-play-experiment`
- **Type**: String
- **Default**: Current experiment name
- **Description**: Experiment name to always play against the latest model from.

#### `--latest-self-play-deterministic-percent`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Percentage of latest self-play that uses deterministic actions.

#### `--latest-self-play-delay-chance`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Probability of adding input delay to latest target agents.

#### `--latest-self-override-env-kwargs`
- **Type**: JSON Dictionary
- **Default**: `{}`
- **Description**: Environment kwargs overrides specifically for latest self-play agents.

---

## Training Parameters (PPO)

### Core PPO Hyperparameters

#### `--learning-rate`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0003)`
- **Description**: Optimizer learning rate for gradient descent.

#### `--batch-size`
- **Type**: Schedule
- **Default**: `ConstantSchedule(256)`
- **Description**: Number of items in each minibatch during training.

#### `--grad-accum`
- **Type**: Schedule
- **Default**: `ConstantSchedule(1)`
- **Description**: Number of batches to accumulate and average gradients over.

#### `--epochs`
- **Type**: Schedule
- **Default**: `ConstantSchedule(1)`
- **Description**: Number of times to train on the sampled rollout data.

#### `--gamma`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.99)`
- **Description**: Discount factor for future rewards.

#### `--gae-lambda`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.95)`
- **Description**: GAE (Generalized Advantage Estimation) lambda parameter for advantage calculation.

#### `--clip-coef`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.2)`
- **Description**: PPO policy clip coefficient (epsilon in PPO paper).

#### `--value-coef`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.5)`
- **Description**: Coefficient for value loss in the total loss function.

#### `--entropy-coef`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Coefficient for entropy bonus to encourage exploration.

#### `--max-grad-norm`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.5)`
- **Description**: Maximum gradient norm for gradient clipping per update.

### Normalization

#### `--normalize-advantages`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Normalize advantages during training for more stable learning.

#### `--normalize-rewards`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Normalize rewards using a running standard deviation of cumulative rewards.

#### `--normalize-observations`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Normalize observations using running mean/std. Can only be set at experiment start.

### Training Behavior

#### `--eps-greedy`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Probability of using deterministic (greedy) sampling when collecting rollouts.

#### `--checkpoint-frequency`
- **Type**: Schedule
- **Default**: `ConstantSchedule(1)`
- **Description**: Number of training rollouts between each model checkpoint save.

#### `--optimize-old-models`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Optimize old model checkpoints by making them non-trainable (saves memory).

#### `--device`
- **Type**: String
- **Default**: `"cuda"` if available, else `"cpu"`
- **Description**: Device to use for training (cuda/cpu).

---

## Network Architecture

### Policy Network Configuration

#### `--share-feature-extractor`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Share feature extractor between actor and critic networks.

#### `--include-target-obs-in-critic`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Include observations of the opponent in the critic network.

#### `--feature-extractor`
- **Type**: JSON Dictionary
- **Default**: `{}`
- **Description**: Feature extractor network configuration.

#### `--actor`
- **Type**: JSON Dictionary
- **Default**: `{"type": "mlp", "hidden_sizes": [64, 64]}`
- **Description**: Actor (policy) network hidden layer configuration.

#### `--action-heads`
- **Type**: JSON Dictionary
- **Default**: `{}`
- **Description**: Action head-specific network configurations.

#### `--critic`
- **Type**: JSON Dictionary
- **Default**: `{"type": "mlp", "hidden_sizes": [64, 64]}`
- **Description**: Critic (value function) network hidden layer configuration.

#### `--policy-kwargs`
- **Type**: JSON Dictionary
- **Default**: `{}`
- **Description**: Additional keyword arguments to pass when initializing the policy.

#### `--add-win-rate-extension`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Add a model extension to predict win probability.

---

## Reward Shaping

### Basic Rewards

#### `--default-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Default reward given at each timestep.

#### `--win-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(1.0)`
- **Description**: Reward for winning the match.

#### `--lose-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(-1.0)`
- **Description**: Reward for losing the match.

#### `--tie-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(-0.2)`
- **Description**: Reward for a tie/draw.

### Combat Rewards

#### `--damage-dealt-reward-scale`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward scaling for damage dealt to opponent.

#### `--damage-received-reward-scale`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward scaling for damage received from opponent (usually negative).

#### `--reward-on-damage-generated`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Reward/penalize damage when it is generated instead of when it appears.

#### `--reward-on-hit-with-boost-scale`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward scale when hitting with offensive stat boosts active.

### Prayer Rewards

#### `--protected-correct-prayer-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward for protecting against the correct attack style.

#### `--protected-wrong-prayer-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward for protecting against the wrong attack style.

#### `--attacked-correct-prayer-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward for attacking when opponent is protecting correctly.

#### `--attacked-wrong-prayer-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward for attacking when opponent is protecting incorrectly.

#### `--protected-previous-correct-prayer-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward for protecting against the attack style used in the previous tick.

#### `--protected-previous-wrong-prayer-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward for protecting against the wrong previous attack style.

#### `--attacked-previous-correct-prayer-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward when opponent protected correctly against previous attack.

#### `--attacked-previous-wrong-prayer-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward when opponent protected incorrectly against previous attack.

#### `--no-prayer-tick-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward (or penalty) for having no prayer active for a tick.

#### `--smite-damage-dealt-reward-multiplier`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Multiplier for damage dealt reward when smite prayer is active.

#### `--smite-damage-received-reward-multiplier`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Multiplier for damage received reward when opponent has smite active.

### Food & HP Management

#### `--penalize-food-on-death`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Penalize agent for dying with food remaining.

#### `--reward-target-food-on-death`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Reward agent when opponent dies with food remaining.

#### `--penalize-wasted-food`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Penalize eating food when already at/near max HP.

#### `--player-died-with-food-multiplier`
- **Type**: Schedule
- **Default**: `ConstantSchedule(1.0)`
- **Description**: Multiplier for player dying with food/brews remaining.

#### `--player-wasted-food-multiplier`
- **Type**: Schedule
- **Default**: `ConstantSchedule(1.0)`
- **Description**: Multiplier for player wasting food/brews.

#### `--reward-heals`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Reward heals from damage (e.g., Blood Barrage).

#### `--penalize-target-heals`
- **Type**: Boolean
- **Default**: `True`
- **Description**: Penalize when opponent heals from damage (e.g., Blood Barrage).

### Status Effect Rewards

#### `--target-frozen-tick-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward for each tick the opponent is frozen.

#### `--player-frozen-tick-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward (usually negative) for each tick the agent is frozen.

#### `--safe-penalty`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Penalty for playing too safely/passively.

### Stat Boost Rewards

#### `--attack-level-scale-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward scaling based on attack level boosts.

#### `--strength-level-scale-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward scaling based on strength level boosts.

#### `--defense-level-scale-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward scaling based on defense level boosts.

#### `--ranged-level-scale-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward scaling based on ranged level boosts.

#### `--magic-level-scale-reward`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Reward scaling based on magic level boosts.

### Advanced Rewards

#### `--custom-reward-function`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Custom reward function. Various environment information is passed as input parameters.

#### `--novelty-reward-scale`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Scale factor for novelty-based rewards to encourage exploration.

#### `--action-mask-override`
- **Type**: Schedule
- **Default**: `None`
- **Description**: Override for action masking behavior.

#### `--noise-generator`
- **Type**: Function
- **Default**: `None`
- **Description**: Noise generator function for exploration.

---

## Evaluation & Testing

### Evaluation Environments

#### `--num-eval-agent`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0)`
- **Description**: Number of evaluation agents to run against baseline.

#### `--eval-deterministic-percent`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0.0)`
- **Description**: Percentage of evaluation that uses deterministic (greedy) actions.

#### `--eval-override-env-kwargs`
- **Type**: JSON Dictionary
- **Default**: `{}`
- **Description**: Environment kwargs overrides specifically for evaluation.

#### `--num-reference-rating-envs`
- **Type**: Schedule
- **Default**: `ConstantSchedule(0)`
- **Description**: Number of environments to generate Elo-style ratings against reference agents.

### Exploiter Training

#### `--train-main-exploiter`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Train an exploiter model specifically to beat the main model.

#### `--num-main-exploiters`
- **Type**: Integer
- **Default**: `1`
- **Description**: Number of main exploiter agents to train, if enabled.

#### `--main-exploiter-preset`
- **Type**: String
- **Default**: `None`
- **Description**: Config preset name for training main exploiter.

#### `--main-exploiter-delay`
- **Type**: Integer
- **Default**: `0`
- **Description**: Number of rollouts to wait before starting main exploiter training.

#### `--train-league-exploiter`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Train an exploiter model to beat all models in the league.

#### `--num-league-exploiters`
- **Type**: Integer
- **Default**: `1`
- **Description**: Number of league exploiter agents to train, if enabled.

#### `--league-exploiter-preset`
- **Type**: String
- **Default**: `None`
- **Description**: Config preset name for training league exploiter.

#### `--league-exploiter-delay`
- **Type**: Integer
- **Default**: `0`
- **Description**: Number of rollouts to wait before starting league exploiter training.

### Debugging & Monitoring

#### `--early-stopping`
- **Type**: Schedule
- **Default**: `None`
- **Description**: Early stopping condition configuration.

#### `--enable-tracking-histograms`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Enable tracking histograms in TensorBoard. Causes performance hit when viewing in TensorBoard.

#### `--save-latest-buffer`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Save the latest rollout buffer to a file for debugging.

#### `--save-latest-meta`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Save the latest metadata to a file.

---

## Distributed Training

### Remote Processing

#### `--remote-processor-pool-size`
- **Type**: Integer
- **Default**: `0`
- **Description**: Size of remote processor pool for parallel inference.

#### `--remote-processor-device`
- **Type**: String
- **Default**: `"cuda"` if available, else `"cpu"`
- **Description**: Device for remote processor (cuda/cpu).

#### `--remote-processor-type`
- **Type**: String
- **Default**: `"thread"`
- **Choices**: `"thread"`, `"ray"`
- **Description**: Type of remote processor to use for distributed inference.

#### `--remote-processor-kwargs`
- **Type**: JSON Dictionary
- **Default**: `{}`
- **Description**: Additional kwargs for remote processor configuration.

### Distributed Rollouts

#### `--distributed-rollouts`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Use distributed rollout sampling system across a fleet of CPUs.

#### `--distributed-rollout-preset`
- **Type**: String
- **Default**: `""`
- **Description**: Preset to use for rollout sampling. Required if using distributed rollouts (overrides many settings).

#### `--num-distributed-rollouts`
- **Type**: Integer
- **Default**: `0`
- **Description**: Number of parallel distributed rollouts. Defaults to filling available resources (no autoscaling).

#### `--num-cpus-per-rollout`
- **Type**: Integer
- **Default**: `2` (with GPU) or `4` (CPU only)
- **Description**: Number of CPUs to allocate to each distributed rollout worker.

#### `--forward-distribution-to-exploiters`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Forward distributed rollouts to exploiter training.

---

## Advanced Options

### Bootstrapping

#### `--bootstrap-from-experiment`
- **Type**: String
- **Default**: `None`
- **Description**: Experiment name to bootstrap from (starts with that experiment's latest model).

---

## Schedule Types

Many parameters accept a **Schedule** type, which allows values to change over time. Common schedule formats:

- **Constant**: `"10"` or `ConstantSchedule(10)` - Fixed value
- **Linear**: `"linear(start=1.0,end=0.1,steps=1000000)"` - Linear interpolation
- **Exponential**: `"exp(start=1.0,end=0.01,steps=1000000)"` - Exponential decay
- **Step**: `"step(start=1.0,end=0.1,steps=1000000,decay=0.5)"` - Step decay

---

## Example Usage

### Basic Self-Play Training
```bash
python train.py \
  --experiment-name my-first-experiment \
  --env-name NhEnv \
  --num-envs 10 \
  --self-play-percent 1.0 \
  --learning-rate 0.0003 \
  --train-rollouts 1000
```

### Past Self-Play with Curriculum
```bash
python train.py \
  --experiment-name curriculum-experiment \
  --env-name NhEnv \
  --num-envs 20 \
  --self-play-percent 0.5 \
  --past-self-play-percent 0.5 \
  --past-self-play-experiment baseline-experiment \
  --learning-rate "linear(start=0.001,end=0.0001,steps=5000000)"
```

### Distributed Training with Exploiter
```bash
python train.py \
  --experiment-name distributed-exp \
  --distributed-rollouts \
  --distributed-rollout-preset nh-distributed \
  --num-distributed-rollouts 8 \
  --train-main-exploiter \
  --num-main-exploiters 2 \
  --main-exploiter-delay 100
```

### Continue Training with Custom Rewards
```bash
python train.py \
  --experiment-name reward-shaping \
  --continue-training \
  --damage-dealt-reward-scale 0.01 \
  --damage-received-reward-scale -0.01 \
  --protected-correct-prayer-reward 0.05 \
  --target-frozen-tick-reward 0.02
```

---

## Tips

1. **Start Simple**: Begin with basic self-play and default hyperparameters
2. **Use Schedules**: Decay learning rate and exploration over time for better convergence
3. **Monitor TensorBoard**: Track metrics to tune rewards and hyperparameters
4. **Save Checkpoints**: Use `--checkpoint-frequency` to save models regularly
5. **Past Self-Play**: Helps with stability and prevents forgetting previous strategies
6. **Exploiters**: Use exploiters to find weaknesses in your main model
7. **Distributed Training**: Scale up with `--distributed-rollouts` for faster training

For more examples, see the config files in `pvp-ml/config/`.

