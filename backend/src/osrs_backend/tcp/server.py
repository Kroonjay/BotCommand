"""TCP server for ML model inference.

This module provides a TCP socket server for low-latency model inference,
designed for real-time OSRS PvP combat decisions.
"""

import asyncio
import dataclasses
import itertools
import json
import logging
import os
import random
import time
from asyncio import StreamReader, StreamWriter
from pathlib import Path

import torch as th

from osrs_backend.tcp.protocol import InferenceRequest, InferenceResponse
from osrs_backend.config import get_settings
from osrs_backend.ml import create_remote_processor, THREAD_REMOTE_PROCESSOR

logger = logging.getLogger(__name__)


class TCPInferenceServer:
    """TCP server for ML model inference."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9999,
        models_dir: str | None = None,
        pool_size: int = 1,
        processor_type: str = THREAD_REMOTE_PROCESSOR,
        device: str = "cpu",
    ):
        self.host = host
        self.port = port
        self.pool_size = pool_size
        self.processor_type = processor_type
        self.device = device
        self.server = None
        self.remote_processor = None

        # Load models
        settings = get_settings()
        models_path = Path(models_dir or settings.models_dir)
        if models_path.exists():
            self.models = {
                os.path.splitext(filename)[0]: str(models_path / filename)
                for filename in os.listdir(models_path)
                if filename.endswith(".zip")
            }
        else:
            logger.warning(f"Models directory not found: {models_path}")
            self.models = {}

    async def start(self) -> None:
        """Start the TCP server."""
        self.remote_processor = await create_remote_processor(
            pool_size=self.pool_size,
            processor_type=self.processor_type,
            device=self.device,
        )

        # Preload models
        if self.models:
            await self._preload_models()

        self.server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        logger.info(f"TCP inference server started on {self.host}:{self.port}")
        logger.info(f"Available models: {list(self.models.keys())}")

    async def _preload_models(self) -> None:
        """Preload all models into workers."""
        if not self.remote_processor:
            return

        logger.info(
            f"Preloading {len(self.models)} models on {self.remote_processor.get_pool_size()} workers"
        )
        preload_tasks = [
            self.remote_processor.predict(process_id=i, model_path=model)
            for i in range(self.remote_processor.get_pool_size())
            for model in self.models.values()
        ]
        await asyncio.gather(*preload_tasks)
        logger.info("Models preloaded successfully")

    async def stop(self) -> None:
        """Stop the TCP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("TCP inference server stopped")

        if self.remote_processor:
            await self.remote_processor.close()

    async def _handle_client(
        self, reader: StreamReader, writer: StreamWriter
    ) -> None:
        """Handle a connected client."""
        client_ip, client_port, *_ = writer.get_extra_info("peername")
        client_id = f"{client_ip}:{client_port}"
        logger.info(f"[{client_id}] Client connected")

        try:
            while True:
                request_line = await reader.readline()
                if not request_line:
                    break

                logger.debug(f"[{client_id}] Received request: {request_line!r}")

                try:
                    request_json = json.loads(request_line)
                    request = InferenceRequest(**request_json)
                    response = await self._process_request(request, client_id)
                    response_json = dataclasses.asdict(response)
                    response_line = (json.dumps(response_json) + "\n").encode()
                    writer.write(response_line)
                    await writer.drain()
                except Exception as e:
                    logger.error(f"[{client_id}] Error processing request: {e}")
                    error_response = {"error": str(e)}
                    writer.write((json.dumps(error_response) + "\n").encode())
                    await writer.drain()

        except OSError as e:
            logger.warning(f"[{client_id}] Connection error: {e}")
        except Exception as e:
            logger.exception(f"[{client_id}] Unexpected error: {e}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            logger.info(f"[{client_id}] Client disconnected")

    async def _process_request(
        self, request: InferenceRequest, client_id: str
    ) -> InferenceResponse:
        """Process an inference request."""
        model_name = request.model

        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self.models.keys())}")

        logger.info(f"[{client_id}] Generating prediction using model: {model_name}")
        start_time = time.time()

        # Flatten action masks
        raw_sliced_action_masks = request.actionMasks
        raw_action_masks = list(itertools.chain.from_iterable(raw_sliced_action_masks))

        observations = th.tensor([request.obs], dtype=th.float32, device="cpu")
        action_masks = th.tensor([raw_action_masks], dtype=th.bool, device="cpu")

        sample_deterministic: bool | th.Tensor
        if isinstance(request.deterministic, list):
            sample_deterministic = th.tensor(
                request.deterministic, dtype=th.bool, device="cpu"
            )
        else:
            sample_deterministic = request.deterministic

        random_pool_worker = random.randint(
            0, self.remote_processor.get_pool_size() - 1
        )

        model_path = self.models[model_name]
        (
            action,
            log_probs,
            entropy,
            values,
            flattened_probs,
            ext_results,
        ) = await self.remote_processor.predict(
            observation=observations,
            deterministic=sample_deterministic,
            action_masks=action_masks,
            process_id=random_pool_worker,
            model_path=model_path,
            return_actions=True,
            return_log_probs=request.returnLogProb,
            return_entropy=request.returnEntropy,
            return_values=request.returnValue,
            return_probs=request.returnProbs,
            extensions=request.extensions,
        )
        assert action is not None

        # Convert flattened probs to action head sizes
        probs = None
        if request.returnProbs and flattened_probs is not None:
            action_head_sizes = [
                len(action_head) for action_head in raw_sliced_action_masks
            ]
            cumulative_sizes = [0] + list(itertools.accumulate(action_head_sizes))
            probs = [
                flattened_probs[0, cumulative_sizes[i] : cumulative_sizes[i + 1]].tolist()
                for i in range(len(action_head_sizes))
            ]

        response = InferenceResponse(
            action=action.tolist()[0],
            logProb=log_probs.tolist()[0] if log_probs is not None else None,
            entropy=entropy.tolist()[0] if entropy is not None else None,
            values=values.tolist()[0] if values is not None else None,
            probs=probs,
            extensionResults=ext_results,
        )

        time_elapsed = time.time() - start_time
        logger.info(
            f"[{client_id}] Generated response in {time_elapsed:.4f} seconds: {response.action}"
        )

        return response


async def create_tcp_server(
    host: str = "127.0.0.1",
    port: int = 9999,
    models_dir: str | None = None,
    pool_size: int = 1,
    processor_type: str = THREAD_REMOTE_PROCESSOR,
    device: str = "cpu",
) -> TCPInferenceServer:
    """Create and start a TCP inference server."""
    server = TCPInferenceServer(
        host=host,
        port=port,
        models_dir=models_dir,
        pool_size=pool_size,
        processor_type=processor_type,
        device=device,
    )
    await server.start()
    return server
