"""PPO model container for inference."""

import abc
import dataclasses
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Any, cast

import torch as th

from osrs_backend.ml.contract_loader import ActionDependencies
from osrs_backend.ml.mlp_helper import MlpConfig, default_mlp_config
from osrs_backend.ml.policy import Policy
from osrs_backend.ml.running_mean_std import TensorRunningMeanStd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PolicyParams:
    max_sequence_length: int
    actor_input_size: int
    critic_input_size: int
    action_head_sizes: list[int]
    feature_extractor_config: MlpConfig = field(default_factory=lambda: MlpConfig())
    share_feature_extractor: bool = False
    critic_config: MlpConfig = field(
        default_factory=lambda: default_mlp_config([64, 64])
    )
    actor_config: MlpConfig = field(
        default_factory=lambda: default_mlp_config([128, 128, 128])
    )
    action_head_configs: MlpConfig | list[MlpConfig] | None = None
    action_dependencies: ActionDependencies = field(default_factory=dict)
    autoregressive_actions: bool = True
    append_future_action_masks: bool = False
    normalize_autoregressive_actions: bool = True


@dataclass
class Meta:
    running_observation_stats: TensorRunningMeanStd
    normalized_observations: bool
    trained_steps: int = 0
    trained_rollouts: int = 0
    num_updates: int = 0
    custom_data: dict[str, Any] = field(default_factory=dict)


class ModelExtension(abc.ABC):
    """Base class for model extensions (e.g., win rate prediction)."""

    @abc.abstractmethod
    def run_extension(self, obs: th.Tensor) -> Any:
        pass

    def state_dict(self) -> dict[str, Any]:
        return {}

    def eval(self) -> None:
        pass

    def to(self, device: str) -> None:
        pass

    @classmethod
    def optimize_for_inference(cls, state_dict: dict[str, Any]) -> None:
        pass


# th.jit.compile seems to not be threadsafe
_jit_lock = threading.Lock()
_JIT_EVAL_POLICY = os.getenv("TORCH_SCRIPT_INFERENCE", "true").lower() == "true"


class PPO:
    """PPO model container optimized for inference."""

    def __init__(
        self,
        policy_params: PolicyParams,
        meta: Meta,
        device: str = "cpu",
        trainable: bool = False,
        policy_state: dict[str, Any] | None = None,
        extensions: dict[str, ModelExtension] = {},
    ):
        self._policy_params = policy_params
        self.device = device
        self.meta = meta
        self._extensions = extensions

        # Create and load policy
        policy = Policy(**dataclasses.asdict(policy_params))
        policy.to(device=th.device(device))
        policy.eval()

        if policy_state is not None:
            policy.load_state_dict(policy_state)

        for extension in self._extensions.values():
            extension.to(device)
            extension.eval()

        # Optimize for inference with TorchScript
        if _JIT_EVAL_POLICY:
            with _jit_lock:
                self._eval_policy = th.jit.freeze(th.jit.script(policy))
        else:
            self._eval_policy = policy

    def predict(
        self,
        obs: th.Tensor,
        action_masks: th.Tensor,
        deterministic: bool | th.Tensor = False,
        return_device: str | None = None,
        return_actions: bool = True,
        return_log_probs: bool = True,
        return_entropy: bool = True,
        return_values: bool = True,
        return_probs: bool = False,
        extensions: list[str] = [],
    ) -> tuple[
        th.Tensor | None,
        th.Tensor | None,
        th.Tensor | None,
        th.Tensor | None,
        th.Tensor | None,
        list[Any],
    ]:
        with th.inference_mode():
            obs = obs.to(self.device)
            action_masks = action_masks.to(self.device)

            if deterministic is True:
                deterministic = th.ones(
                    len(self._policy_params.action_head_sizes),
                    dtype=th.bool,
                    device=self.device,
                )
            elif deterministic is False:
                deterministic = th.zeros(
                    len(self._policy_params.action_head_sizes),
                    dtype=th.bool,
                    device=self.device,
                )

            if self.meta.normalized_observations:
                obs = self.meta.running_observation_stats.normalize(obs, clip=True)

            actions, log_probs, entropy, values, probs = self._eval_policy(
                obs,
                action_masks,
                sample_deterministic=deterministic,
                return_actions=return_actions,
                return_entropy=return_entropy,
                return_log_probs=return_log_probs,
                return_values=return_values,
                return_probs=return_probs,
            )

            extension_results = [
                self._extensions[extension].run_extension(obs)
                for extension in extensions
            ]

            if return_device is not None:
                if actions is not None:
                    actions = actions.to(return_device)
                if log_probs is not None:
                    log_probs = log_probs.to(return_device)
                if entropy is not None:
                    entropy = entropy.to(return_device)
                if values is not None:
                    values = values.to(return_device)
                if probs is not None:
                    probs = probs.to(return_device)

            return actions, log_probs, entropy, values, probs, extension_results

    def has_extension(self, name: str) -> bool:
        return name in self._extensions

    @staticmethod
    def load(
        load_path: str, device: str = "cpu", trainable: bool = False
    ) -> "PPO":
        """Load a model from disk for inference."""
        if not os.path.exists(load_path):
            raise ValueError(f"{load_path} not found")

        checkpoint = th.load(load_path, map_location=device, weights_only=False)

        return PPO(
            policy_params=checkpoint["policy_params"],
            meta=checkpoint["meta"],
            device=device,
            trainable=False,  # Always non-trainable for inference
            policy_state=checkpoint["policy"],
            extensions={
                saved_extension["name"]: saved_extension["type"](
                    **saved_extension["params"]
                )
                for saved_extension in checkpoint.get("extensions", [])
            },
        )

    @staticmethod
    def load_meta(load_path: str) -> Meta:
        """Load only model metadata (faster than full load)."""
        if not os.path.exists(load_path):
            raise ValueError(f"{load_path} not found")
        checkpoint = th.load(load_path, map_location="cpu", weights_only=False)
        return cast(Meta, checkpoint["meta"])

    def __str__(self) -> str:
        return f"PPO(device={self.device}, extensions={list(self._extensions.keys())})"
