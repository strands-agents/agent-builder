"""Create instance of SDK's Bedrock model provider."""

from strands.models import BedrockModel
from strands.types.models import Model
from typing_extensions import Unpack


def instance(**model_config: Unpack[BedrockModel.BedrockConfig]) -> Model:
    """Create instance of SDK's Bedrock model provider.

    Args:
        **model_config: Configuration options for the Bedrock model.

    Returns:
        Bedrock model provider.
    """

    return BedrockModel(**model_config)
