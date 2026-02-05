"""TCP protocol data classes for ML inference."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class InferenceRequest:
    """Request for model inference."""

    # The model name to use (can be a plugin name instead).
    model: str
    # The action masks (a list of actions for each action head).
    actionMasks: list[list[bool]]
    # The observations for the current state (a list of each frame - outer list length > 1 if frame stacking).
    obs: list[list[float | int | bool]]
    # Whether to sample deterministically. Can be a list to configure on each action head individually.
    deterministic: list[bool] | bool = False
    # This will return the log probability for taking the current action in the response.
    returnLogProb: bool = False
    # This will return the entropy for each action head distribution in the response.
    returnEntropy: bool = False
    # This will return the value estimate for the current state in the response.
    returnValue: bool = False
    # This will return the raw probabilities for each action in each action head in the response.
    returnProbs: bool = False
    # A list of model extensions to run. Results will be included in the response in the order here.
    extensions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class InferenceResponse:
    """Response from model inference."""

    # The generated action.
    action: list[int]
    # The log probability for taking the current action, if returnLogProb is True in the request.
    logProb: float | None
    # The entropy for each action head distribution if returnEntropy is True in the request.
    entropy: list[float] | None
    # The value estimate for the current state if returnValue is True in the request.
    values: list[float] | None
    # The raw probabilities for each action in each action head if returnProbs is True in the request.
    probs: list[list[float]] | None
    # The results of each model extension specified in the request, in the order the extensions were specified.
    extensionResults: list[Any]
