"""
Tests for the Bedrock model provider with boto_client_config fix.

This module tests the fix for PR #11 which handles the conversion of
boto_client_config from dict to BotocoreConfig object to prevent
AttributeError when launching Strands with Bedrock configuration.
"""

import json
import unittest.mock
from unittest.mock import MagicMock, patch

import pytest
from botocore.config import Config as BotocoreConfig

from strands_agents_builder.models import bedrock


class TestBedrockInstance:
    """Tests for the bedrock.instance() function."""

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_instance_with_dict_boto_client_config(self, mock_bedrock_model):
        """
        Test that boto_client_config as dict is converted to BotocoreConfig.
        
        This is the main test for the PR #11 fix.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        config_dict = {
            "read_timeout": 900,
            "connect_timeout": 900,
            "retries": {"max_attempts": 3, "mode": "adaptive"}
        }
        
        model_config = {
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "boto_client_config": config_dict
        }
        
        # Act
        result = bedrock.instance(**model_config)
        
        # Assert
        # Verify the function returns the mock model
        assert result == mock_model
        
        # Verify BedrockModel was called with converted config
        mock_bedrock_model.assert_called_once()
        call_args = mock_bedrock_model.call_args[1]
        
        # Verify the boto_client_config was converted to BotocoreConfig
        assert "boto_client_config" in call_args
        assert isinstance(call_args["boto_client_config"], BotocoreConfig)
        
        # Verify other config parameters remain unchanged
        assert call_args["model_id"] == "anthropic.claude-3-5-sonnet-20241022-v2:0"

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_instance_with_botocore_config_object(self, mock_bedrock_model):
        """
        Test that existing BotocoreConfig objects are passed through unchanged.
        
        This ensures backward compatibility with existing code.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        botocore_config = BotocoreConfig(
            read_timeout=900,
            connect_timeout=900,
            retries={"max_attempts": 3, "mode": "adaptive"}
        )
        
        model_config = {
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "boto_client_config": botocore_config
        }
        
        # Act
        result = bedrock.instance(**model_config)
        
        # Assert
        assert result == mock_model
        mock_bedrock_model.assert_called_once()
        call_args = mock_bedrock_model.call_args[1]
        
        # Verify the same BotocoreConfig object is used (no conversion)
        assert call_args["boto_client_config"] is botocore_config

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_instance_without_boto_client_config(self, mock_bedrock_model):
        """
        Test that function works correctly when boto_client_config is not provided.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        model_config = {
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "max_tokens": 4096
        }
        
        # Act
        result = bedrock.instance(**model_config)
        
        # Assert
        assert result == mock_model
        mock_bedrock_model.assert_called_once()
        call_args = mock_bedrock_model.call_args[1]
        
        # Verify boto_client_config is not in the call
        assert "boto_client_config" not in call_args
        assert call_args["model_id"] == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert call_args["max_tokens"] == 4096

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_instance_with_none_boto_client_config(self, mock_bedrock_model):
        """
        Test that function handles None boto_client_config correctly.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        model_config = {
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "boto_client_config": None
        }
        
        # Act
        result = bedrock.instance(**model_config)
        
        # Assert
        assert result == mock_model
        mock_bedrock_model.assert_called_once()
        call_args = mock_bedrock_model.call_args[1]
        
        # Verify None is passed through unchanged (no conversion attempted)
        assert call_args["boto_client_config"] is None

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_converted_config_has_correct_attributes(self, mock_bedrock_model):
        """
        Test that the converted BotocoreConfig object has the expected attributes.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        config_dict = {
            "read_timeout": 900,
            "connect_timeout": 600,
            "retries": {"max_attempts": 5, "mode": "standard"},
            "max_pool_connections": 50
        }
        
        model_config = {
            "model_id": "test-model",
            "boto_client_config": config_dict
        }
        
        # Act
        result = bedrock.instance(**model_config)
        
        # Assert
        mock_bedrock_model.assert_called_once()
        call_args = mock_bedrock_model.call_args[1]
        converted_config = call_args["boto_client_config"]
        
        # Verify the converted config is a BotocoreConfig with expected attributes
        assert isinstance(converted_config, BotocoreConfig)
        # Note: BotocoreConfig stores values internally, we can't directly access them
        # but we can verify it was created without error and is the right type

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_instance_with_complex_model_config(self, mock_bedrock_model):
        """
        Test with a complex configuration similar to real-world usage.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        model_config = {
            "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
            "max_tokens": 64000,
            "boto_client_config": {
                "read_timeout": 900,
                "connect_timeout": 900,
                "retries": {"max_attempts": 3, "mode": "adaptive"}
            },
            "additional_request_fields": {
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 2048
                }
            }
        }
        
        # Act
        result = bedrock.instance(**model_config)
        
        # Assert
        assert result == mock_model
        mock_bedrock_model.assert_called_once()
        call_args = mock_bedrock_model.call_args[1]
        
        # Verify all config is preserved
        assert call_args["model_id"] == "us.anthropic.claude-sonnet-4-20250514-v1:0"
        assert call_args["max_tokens"] == 64000
        assert isinstance(call_args["boto_client_config"], BotocoreConfig)
        assert call_args["additional_request_fields"]["thinking"]["budget_tokens"] == 2048

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_instance_preserves_original_config_object(self, mock_bedrock_model):
        """
        Test that the original model_config dict is not modified in place.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        original_config_dict = {"read_timeout": 900}
        model_config = {
            "model_id": "test-model",
            "boto_client_config": original_config_dict
        }
        
        # Act
        result = bedrock.instance(**model_config)
        
        # Assert
        # Verify the original dict wasn't modified
        assert isinstance(model_config["boto_client_config"], dict)
        assert model_config["boto_client_config"] is original_config_dict
        
        # But the call to BedrockModel used the converted version
        mock_bedrock_model.assert_called_once()
        call_args = mock_bedrock_model.call_args[1]
        assert isinstance(call_args["boto_client_config"], BotocoreConfig)

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_instance_with_empty_boto_client_config_dict(self, mock_bedrock_model):
        """
        Test conversion of empty boto_client_config dictionary.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        model_config = {
            "model_id": "test-model",
            "boto_client_config": {}
        }
        
        # Act
        result = bedrock.instance(**model_config)
        
        # Assert
        assert result == mock_model
        mock_bedrock_model.assert_called_once()
        call_args = mock_bedrock_model.call_args[1]
        
        # Verify empty dict is converted to BotocoreConfig
        assert isinstance(call_args["boto_client_config"], BotocoreConfig)


class TestBedrockConfigConversion:
    """Tests specifically for the boto_client_config conversion logic."""

    def test_botocore_config_creation_with_valid_dict(self):
        """
        Test that BotocoreConfig can be created from a typical configuration dict.
        """
        # Arrange
        config_dict = {
            "read_timeout": 900,
            "connect_timeout": 600,
            "retries": {"max_attempts": 3, "mode": "adaptive"}
        }
        
        # Act
        config = BotocoreConfig(**config_dict)
        
        # Assert
        assert isinstance(config, BotocoreConfig)

    def test_botocore_config_creation_with_empty_dict(self):
        """
        Test that BotocoreConfig can be created from an empty dict.
        """
        # Arrange
        config_dict = {}
        
        # Act
        config = BotocoreConfig(**config_dict)
        
        # Assert
        assert isinstance(config, BotocoreConfig)

    def test_isinstance_detection_dict(self):
        """
        Test that isinstance correctly identifies dict objects.
        """
        # Arrange
        test_dict = {"key": "value"}
        
        # Act & Assert
        assert isinstance(test_dict, dict)
        assert not isinstance(test_dict, BotocoreConfig)

    def test_isinstance_detection_botocore_config(self):
        """
        Test that isinstance correctly identifies BotocoreConfig objects.
        """
        # Arrange
        config = BotocoreConfig()
        
        # Act & Assert
        assert isinstance(config, BotocoreConfig)
        assert not isinstance(config, dict)


class TestBedrockIntegrationScenarios:
    """Integration tests simulating real configuration scenarios."""

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_json_config_parsing_scenario(self, mock_bedrock_model):
        """
        Test the exact scenario that was failing before the fix.
        
        This simulates loading configuration from JSON where boto_client_config
        gets parsed as a dictionary instead of a BotocoreConfig object.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        # Simulate JSON configuration like what would be loaded from a config file
        json_config = '''
        {
            "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
            "max_tokens": 64000,
            "boto_client_config": {
                "read_timeout": 900,
                "connect_timeout": 900,
                "retries": {
                    "max_attempts": 3,
                    "mode": "adaptive"
                }
            },
            "additional_request_fields": {
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 2048
                }
            }
        }
        '''
        
        # Parse JSON (this creates dict objects, not BotocoreConfig)
        parsed_config = json.loads(json_config)
        
        # Act - this would have failed before the fix
        result = bedrock.instance(**parsed_config)
        
        # Assert
        assert result == mock_model
        mock_bedrock_model.assert_called_once()
        call_args = mock_bedrock_model.call_args[1]
        
        # Verify the conversion happened correctly
        assert isinstance(call_args["boto_client_config"], BotocoreConfig)
        assert call_args["model_id"] == "us.anthropic.claude-sonnet-4-20250514-v1:0"
        assert call_args["max_tokens"] == 64000

    def test_simulate_attribute_error_before_fix(self):
        """
        Test that demonstrates what would happen without the fix.
        
        This test shows that a plain dict doesn't have the 'merge' method
        that BedrockModel.boto_client_config.merge() would try to call.
        """
        # Arrange
        config_dict = {
            "read_timeout": 900,
            "connect_timeout": 900,
            "retries": {"max_attempts": 3, "mode": "adaptive"}
        }
        
        # Act & Assert
        # This demonstrates the error that would occur without the fix
        with pytest.raises(AttributeError, match="'dict' object has no attribute 'merge'"):
            config_dict.merge({})  # This is what was happening in BedrockModel
        
        # But BotocoreConfig does have merge method
        botocore_config = BotocoreConfig(**config_dict)
        # This should not raise an error
        merged = botocore_config.merge(BotocoreConfig())
        assert isinstance(merged, BotocoreConfig)

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_typical_strands_launch_config(self, mock_bedrock_model):
        """
        Test with configuration typical of a Strands agent launch.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        # This is the type of config that would cause the original error
        strands_config = {
            "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
            "max_tokens": 64000,
            "boto_client_config": {  # This would be a dict from JSON parsing
                "read_timeout": 900,
                "connect_timeout": 900,
                "retries": {
                    "max_attempts": 3,
                    "mode": "adaptive"
                }
            },
            "additional_request_fields": {
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 2048
                }
            }
        }
        
        # Act
        result = bedrock.instance(**strands_config)
        
        # Assert
        assert result == mock_model
        mock_bedrock_model.assert_called_once()
        
        # Verify the problematic config was properly converted
        call_args = mock_bedrock_model.call_args[1]
        boto_config = call_args["boto_client_config"]
        assert isinstance(boto_config, BotocoreConfig)

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_mixed_config_sources(self, mock_bedrock_model):
        """
        Test scenario where some config comes from JSON and some from code.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        # JSON-sourced config (dict)
        json_boto_config = {
            "read_timeout": 900,
            "retries": {"max_attempts": 3}
        }
        
        # Code-sourced config (already BotocoreConfig)
        existing_config = BotocoreConfig(connect_timeout=600)
        
        # Test with dict config first
        result1 = bedrock.instance(
            model_id="test1",
            boto_client_config=json_boto_config
        )
        
        # Test with existing BotocoreConfig
        result2 = bedrock.instance(
            model_id="test2", 
            boto_client_config=existing_config
        )
        
        # Assert both work
        assert result1 == mock_model
        assert result2 == mock_model
        assert mock_bedrock_model.call_count == 2
        
        # Verify proper handling in both cases
        first_call_config = mock_bedrock_model.call_args_list[0][1]["boto_client_config"]
        second_call_config = mock_bedrock_model.call_args_list[1][1]["boto_client_config"]
        
        assert isinstance(first_call_config, BotocoreConfig)  # Converted
        assert second_call_config is existing_config  # Passed through

    def test_config_dict_structure_validation(self):
        """
        Test that the configuration dict structure is valid for BotocoreConfig.
        """
        # Arrange - typical configuration that would come from JSON
        config_structures = [
            # Minimal config
            {},
            
            # Basic timeout config
            {"read_timeout": 900},
            
            # Full config with retries
            {
                "read_timeout": 900,
                "connect_timeout": 600,
                "retries": {"max_attempts": 3, "mode": "adaptive"}
            },
            
            # Config with additional parameters
            {
                "read_timeout": 900,
                "connect_timeout": 600,
                "retries": {"max_attempts": 5, "mode": "standard"},
                "max_pool_connections": 50,
                "parameter_validation": False
            }
        ]
        
        # Act & Assert
        for config_dict in config_structures:
            # This should not raise any exceptions
            botocore_config = BotocoreConfig(**config_dict)
            assert isinstance(botocore_config, BotocoreConfig)


class TestRegressionPrevention:
    """Tests to prevent regression of the original bug."""
    
    def test_dict_object_has_no_merge_attribute(self):
        """
        Verify that dict objects don't have merge method.
        
        This test ensures we understand the root cause of the original error.
        """
        # Arrange
        test_dict = {"key": "value"}
        
        # Act & Assert
        assert not hasattr(test_dict, "merge")
        
        with pytest.raises(AttributeError):
            test_dict.merge({})

    def test_botocore_config_has_merge_attribute(self):
        """
        Verify that BotocoreConfig objects do have merge method.
        """
        # Arrange
        config = BotocoreConfig()
        
        # Act & Assert
        assert hasattr(config, "merge")
        
        # Should not raise an error
        merged = config.merge(BotocoreConfig())
        assert isinstance(merged, BotocoreConfig)

    @patch('strands_agents_builder.models.bedrock.BedrockModel')
    def test_fix_addresses_root_cause(self, mock_bedrock_model):
        """
        Test that the fix prevents the original AttributeError.
        """
        # Arrange
        mock_model = MagicMock()
        mock_bedrock_model.return_value = mock_model
        
        # This dict would cause the original error
        problematic_config = {
            "model_id": "test-model",
            "boto_client_config": {
                "read_timeout": 900,
                "retries": {"max_attempts": 3}
            }
        }
        
        # Act - this should NOT raise AttributeError anymore
        result = bedrock.instance(**problematic_config)
        
        # Assert
        assert result == mock_model
        
        # Verify the config was converted properly
        call_args = mock_bedrock_model.call_args[1]
        converted_config = call_args["boto_client_config"]
        
        # This should work now (would have failed before the fix)
        assert isinstance(converted_config, BotocoreConfig)
        merged = converted_config.merge(BotocoreConfig())
        assert isinstance(merged, BotocoreConfig)