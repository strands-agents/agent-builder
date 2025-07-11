"""Utilities for loading model providers in strands."""

import importlib
import json
import os
import pathlib
from typing import Any

from botocore.config import Config
from strands.models import Model

# Default model configuration
DEFAULT_MODEL_CONFIG = {
    "model_id": os.getenv("STRANDS_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
    "max_tokens": int(os.getenv("STRANDS_MAX_TOKENS", "32768")),
    "boto_client_config": Config(
        read_timeout=900,
        connect_timeout=900,
        retries=dict(max_attempts=3, mode="adaptive"),
    ),
    "additional_request_fields": {
        "thinking": {
            "type": os.getenv("STRANDS_THINKING_TYPE", "enabled"),
            "budget_tokens": int(os.getenv("STRANDS_BUDGET_TOKENS", "2048")),
        },
    },
    "cache_tools": os.getenv("STRANDS_CACHE_TOOLS", "default"),
    "cache_prompt": os.getenv("STRANDS_CACHE_PROMPT", "default"),
}
ANTHROPIC_BETA_FEATURES = os.getenv("STRANDS_ANTHROPIC_BETA", "interleaved-thinking-2025-05-14")
if len(ANTHROPIC_BETA_FEATURES) > 0:
    DEFAULT_MODEL_CONFIG["additional_request_fields"]["anthropic_beta"] = ANTHROPIC_BETA_FEATURES.split(",")


def load_path(name: str) -> pathlib.Path:
    """Locate the model provider module file path.

    First search "$CWD/.models". If the module file is not found, fall back to the built-in models directory.

    Args:
        name: Name of the model provider (e.g., bedrock).

    Returns:
        The file path to the model provider module.

    Raises:
        ImportError: If the model provider module cannot be found.
    """
    path = pathlib.Path.cwd() / ".models" / f"{name}.py"
    if not path.exists():
        path = pathlib.Path(__file__).parent / ".." / "models" / f"{name}.py"

    if not path.exists():
        raise ImportError(f"model_provider=<{name}> | does not exist")

    return path


def load_config(config: str) -> dict[str, Any]:
    """Load model configuration from a JSON string or file.

    Args:
        config: A JSON string or path to a JSON file containing model configuration.
            If empty string or '{}', the default config is used.

    Returns:
        The parsed configuration.
    """
    if not config or config == "{}":
        return DEFAULT_MODEL_CONFIG

    if config.endswith(".json"):
        with open(config) as fp:
            return json.load(fp)

    return json.loads(config)


def load_model(path: pathlib.Path, config: dict[str, Any]) -> Model:
    """Dynamically load and instantiate a model provider from a Python module.

    Imports the module at the specified path and calls its 'instance' function
    with the provided configuration to create a model instance.

    Args:
        path: Path to the Python module containing the model provider implementation.
        config: Configuration to pass to the model provider's instance function.

    Returns:
        An instantiated model provider.
    """
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.instance(**config)
