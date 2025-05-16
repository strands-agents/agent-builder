"""Create instances of SDK model providers.

Module must expose an `instance` function that returns a `strands.types.models.Model` implementation.
"""

from . import bedrock, ollama

__all__ = ["bedrock", "ollama"]
