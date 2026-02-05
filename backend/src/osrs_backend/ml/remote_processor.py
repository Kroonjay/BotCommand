"""Remote processor for model inference with caching and thread pooling."""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any

import torch as th

from osrs_backend.ml.ppo import PPO

logger = logging.getLogger(__name__)

THREAD_REMOTE_PROCESSOR = "thread"
REMOTE_PROCESSOR_TYPES = [THREAD_REMOTE_PROCESSOR]


class RemoteProcessor(ABC):
    """Abstract base class for model inference processors."""

    @abstractmethod
    async def predict(
        self,
        process_id: int,
        model_path: str,
        observation: th.Tensor | None = None,
        action_masks: th.Tensor | None = None,
        deterministic: bool | th.Tensor = False,
        return_device: str | None = None,
        return_actions: bool = True,
        return_log_probs: bool = False,
        return_entropy: bool = False,
        return_values: bool = False,
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
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    def get_pool_size(self) -> int:
        pass

    @abstractmethod
    def get_device(self) -> str:
        pass

    async def __aenter__(self) -> "RemoteProcessor":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


class ThreadedProcessor(RemoteProcessor):
    """Thread-pool based processor for CPU inference."""

    def __init__(self, pool_size: int, device: str = "cpu"):
        self._pool_size = pool_size
        self._device = device
        self._executor = ThreadPoolExecutor(
            max_workers=pool_size,
            thread_name_prefix=f"ml-inference-{str(uuid.uuid4())[:8]}",
        )
        self._model_locks: dict[str, Lock] = {}
        self._models: dict[str, PPO] = {}
        self._lock_lock = Lock()

    def get_pool_size(self) -> int:
        return self._pool_size

    def get_device(self) -> str:
        return self._device

    async def close(self) -> None:
        self._executor.shutdown(wait=True)

    async def predict(
        self,
        process_id: int,
        model_path: str,
        observation: th.Tensor | None = None,
        action_masks: th.Tensor | None = None,
        deterministic: bool | th.Tensor = False,
        return_device: str | None = None,
        return_actions: bool = True,
        return_log_probs: bool = False,
        return_entropy: bool = False,
        return_values: bool = False,
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
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._worker_task,
            model_path,
            observation,
            action_masks,
            deterministic,
            return_device,
            return_actions,
            return_log_probs,
            return_entropy,
            return_values,
            return_probs,
            extensions,
        )

    def _worker_task(
        self,
        model_path: str,
        observation: th.Tensor | None,
        action_masks: th.Tensor | None,
        deterministic: bool,
        return_device: str | None,
        return_actions: bool = True,
        return_log_probs: bool = False,
        return_entropy: bool = False,
        return_values: bool = False,
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
        model = self._load_model(model_path)
        if observation is None:
            # Preload model, don't actually predict
            return None, None, None, None, None, []
        else:
            if return_device is None:
                return_device = str(observation.device)
            assert action_masks is not None
            action_masks = action_masks.to(self._device)
            return model.predict(
                observation.to(self._device),
                action_masks,
                deterministic=deterministic,
                return_actions=return_actions,
                return_values=return_values,
                return_log_probs=return_log_probs,
                return_entropy=return_entropy,
                return_probs=return_probs,
                return_device=return_device,
                extensions=extensions,
            )

    def _load_model(self, model_path: str) -> PPO:
        # Thread-safe model loading with caching
        if model_path not in self._models:
            # Find/create model lock
            with self._lock_lock:
                if model_path not in self._model_locks:
                    self._model_locks[model_path] = Lock()
                model_lock = self._model_locks[model_path]
            with model_lock:
                # Double check model hasn't already loaded
                if model_path not in self._models:
                    load_start_time = time.time()
                    logger.info(f"Loading model {model_path} into memory")
                    self._models[model_path] = PPO.load(
                        model_path, device=self._device, trainable=False
                    )
                    logger.info(
                        f"Loaded model {model_path} in {time.time() - load_start_time:.2f}s"
                    )
            with self._lock_lock:
                # Clean up lock after model loaded
                if model_path in self._model_locks:
                    del self._model_locks[model_path]
        return self._models[model_path]


async def create_remote_processor(
    pool_size: int = 1,
    processor_type: str = THREAD_REMOTE_PROCESSOR,
    device: str = "cpu",
    **kwargs: Any,
) -> RemoteProcessor:
    """Factory function to create a remote processor."""
    if processor_type == THREAD_REMOTE_PROCESSOR:
        return ThreadedProcessor(pool_size=pool_size, device=device)
    raise ValueError(f"Unknown processor type: {processor_type}")
