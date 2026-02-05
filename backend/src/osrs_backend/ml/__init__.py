"""ML inference module for OSRS PvP models."""

from osrs_backend.ml.ppo import PPO, Meta, ModelExtension, PolicyParams
from osrs_backend.ml.remote_processor import (
    RemoteProcessor,
    ThreadedProcessor,
    create_remote_processor,
    THREAD_REMOTE_PROCESSOR,
    REMOTE_PROCESSOR_TYPES,
)
from osrs_backend.ml.contract_loader import (
    EnvironmentMeta,
    ActionHead,
    Action,
    Observation,
    ActionDependencies,
    load_environment_contract,
    set_contracts_dir,
    get_env_types,
)

__all__ = [
    # PPO
    "PPO",
    "Meta",
    "ModelExtension",
    "PolicyParams",
    # Remote Processor
    "RemoteProcessor",
    "ThreadedProcessor",
    "create_remote_processor",
    "THREAD_REMOTE_PROCESSOR",
    "REMOTE_PROCESSOR_TYPES",
    # Contract Loader
    "EnvironmentMeta",
    "ActionHead",
    "Action",
    "Observation",
    "ActionDependencies",
    "load_environment_contract",
    "set_contracts_dir",
    "get_env_types",
]
