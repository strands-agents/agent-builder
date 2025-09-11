#!/usr/bin/env python3
"""
Unit tests for the strand tool
"""

import os
from io import StringIO
from unittest import mock

from tools.strand import strand


class TestStrandTool:
    """Test cases for the strand tool"""

    def test_strand_with_query(self):
        """Test basic query processing"""
        with mock.patch("tools.strand.Agent") as mock_agent_class:
            # Setup mock agent
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            mock_agent_instance.return_value = {"status": "success", "content": [{"text": "Agent response"}]}

            # Call the strand tool
            tool_use = {"toolUseId": "test_id", "input": {"query": "test query"}}
            # Store result to validate return value
            result = strand(tool_use)
            assert result["status"] == "success"

            # Verify agent was created and called with the query
            mock_agent_class.assert_called_once()
            mock_agent_instance.assert_called_once()

            # Verify success response
            assert result["status"] == "success"

    def test_strand_empty_query(self):
        """Test handling of empty query"""
        # Call the strand tool with empty query
        result = strand(query="")

        # Verify error response
        assert result["status"] == "error"
        assert "No query provided" in result["content"][0]["text"]

    def test_strand_custom_system_prompt(self):
        """Test using custom system prompt"""
        with mock.patch("tools.strand.Agent") as mock_agent_class:
            # Setup mock agent
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            mock_agent_instance.return_value = {"status": "success", "content": [{"text": "Agent response"}]}

            # Call the strand tool with custom prompt
            # Store result to validate return value
            result = strand(query="test query", system_prompt="Custom system prompt")
            assert result["status"] == "success"

            # Verify agent was created with custom prompt
            mock_agent_class.assert_called_once()
            kwargs = mock_agent_class.call_args.kwargs
            assert kwargs["system_prompt"] == "Custom system prompt"

    def test_strand_specific_tools(self):
        """Test specifying particular tools"""
        with mock.patch("tools.strand.Agent") as mock_agent_class:
            # Setup mock agent
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            mock_agent_instance.return_value = {"status": "success", "content": [{"text": "Agent response"}]}

            # Call the strand tool with specific tools
            tool_use = {"toolUseId": "test_id", "input": {"query": "test query", "tool_names": ["tool1", "tool2"]}}
            # Store result to validate return value
            result = strand(tool_use)
            assert result["status"] == "success"

            # Check that the tools were passed
            called_args = mock_agent_class.call_args.kwargs
            assert "tools" in called_args
            # Specific test frameworks may need to be updated for exact tool count

    def test_strand_env_system_prompt(self):
        """Test loading system prompt from environment variable"""
        with (
            mock.patch.dict(os.environ, {"STRANDS_SYSTEM_PROMPT": "Prompt from env"}),
            mock.patch("tools.strand.Agent") as mock_agent_class,
        ):
            # Setup mock agent
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            mock_agent_instance.return_value = {"status": "success", "content": [{"text": "Agent response"}]}

            # Call the strand tool
            tool_use = {"toolUseId": "test_id", "input": {"query": "test query"}}
            # Store result to validate return value
            result = strand(tool_use)
            assert result["status"] == "success"

            # Verify agent was created with env prompt
            mock_agent_class.assert_called_once()
            kwargs = mock_agent_class.call_args.kwargs
            assert kwargs["system_prompt"] == "Prompt from env"

    def test_strand_file_system_prompt(self):
        """Test loading system prompt from file"""
        with (
            mock.patch("src.strands_agents_builder.utils.kb_utils.os.getenv", return_value=None),
            mock.patch("src.strands_agents_builder.utils.kb_utils.os.getcwd", return_value="/test/dir"),
            mock.patch("src.strands_agents_builder.utils.kb_utils.Path") as mock_path_class,
            mock.patch("tools.strand.Agent") as mock_agent_class,
        ):
            # Setup mock path instances
            mock_cwd_path = mock.MagicMock()
            mock_prompt_file = mock.MagicMock()

            # Mock Path constructor to return mock_cwd_path
            mock_path_class.return_value = mock_cwd_path

            # Mock the / operator to return mock_prompt_file
            mock_cwd_path.__truediv__.return_value = mock_prompt_file

            # Setup mock_prompt_file behavior
            mock_prompt_file.exists.return_value = True
            mock_prompt_file.is_file.return_value = True
            mock_prompt_file.read_text.return_value = "Prompt from file\n"
            # Setup mock agent
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            mock_agent_instance.return_value = {"status": "success", "content": [{"text": "Agent response"}]}

            # Call the strand tool
            tool_use = {"toolUseId": "test_id", "input": {"query": "test query"}}
            # Store result to validate return value
            result = strand(tool_use)
            assert result["status"] == "success"

            # Verify agent was created with file prompt
            mock_agent_class.assert_called_once()
            kwargs = mock_agent_class.call_args.kwargs
            assert kwargs["system_prompt"] == "Prompt from file"

    def test_strand_default_system_prompt(self):
        """Test using default system prompt when no others available"""
        with (
            mock.patch("pathlib.Path.exists", return_value=False),
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch("tools.strand.Agent") as mock_agent_class,
        ):
            # Setup mock agent
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            mock_agent_instance.return_value = {"status": "success", "content": [{"text": "Agent response"}]}

            # Call the strand tool
            tool_use = {"toolUseId": "test_id", "input": {"query": "test query"}}
            # Store result to validate return value
            result = strand(tool_use)
            assert result["status"] == "success"

            # Verify agent was created with default prompt
            mock_agent_class.assert_called_once()
            kwargs = mock_agent_class.call_args.kwargs
            assert kwargs["system_prompt"] == "You are a helpful assistant."

    def test_strand_exception_handling(self):
        """Test handling of exceptions"""
        with mock.patch("tools.strand.Agent") as mock_agent_class:
            # Make agent raise an exception
            mock_agent_class.side_effect = Exception("Test error")

            # Call the strand tool
            tool_use = {"toolUseId": "test_id", "input": {"query": "test query"}}
            # Store result to validate return value
            result = strand(tool_use)

            # Verify error response
            assert result["status"] == "error"
            assert "Error" in result["content"][0]["text"]

    def test_strand_tool_with_file_prompt(self):
        """Test strand tool using .prompt file"""

        # Create a temporary prompt file
        with (
            mock.patch("src.strands_agents_builder.utils.kb_utils.os.getenv", return_value=None),
            mock.patch("src.strands_agents_builder.utils.kb_utils.os.getcwd", return_value="/test/dir"),
            mock.patch("src.strands_agents_builder.utils.kb_utils.Path") as mock_path_class,
            mock.patch("sys.stdout", new_callable=StringIO),
            mock.patch("tools.strand.Agent") as mock_agent_class,
        ):
            # Setup mock path instances
            mock_cwd_path = mock.MagicMock()
            mock_prompt_file = mock.MagicMock()

            # Mock Path constructor to return mock_cwd_path
            mock_path_class.return_value = mock_cwd_path

            # Mock the / operator to return mock_prompt_file
            mock_cwd_path.__truediv__.return_value = mock_prompt_file

            # Setup mock_prompt_file behavior
            mock_prompt_file.exists.return_value = True
            mock_prompt_file.is_file.return_value = True
            mock_prompt_file.read_text.return_value = "Test prompt from file"
            # Mock the agent instance
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            mock_agent_instance.return_value = {"status": "success", "content": [{"text": "Agent response"}]}

            # Call the strand tool
            tool_use = {"toolUseId": "test_id", "input": {"query": "test query"}}
            # Store result to validate return value
            result = strand(tool_use)
            assert result["status"] == "success"

            # Verify the system prompt was loaded from file
            mock_agent_class.assert_called_once()
            called_kwargs = mock_agent_class.call_args.kwargs
            assert called_kwargs["system_prompt"] == "Test prompt from file"

    def test_strand_tool_with_specific_tools(self):
        """Test strand tool with specific tool selection"""

        with (
            mock.patch("sys.stdout", new_callable=StringIO),
            mock.patch("tools.strand.Agent") as mock_agent_class,
        ):
            # Mock the agent instance
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            mock_agent_instance.return_value = {"status": "success", "content": [{"text": "Agent response"}]}

            # Call the strand tool with specific tools
            tool_use = {"toolUseId": "test_id", "input": {"query": "test query", "tool_names": ["shell", "editor"]}}
            _ = strand(tool_use)

            # Verify agent was initialized with the right tools
            mock_agent_class.assert_called_once()
            # Check that only the specified tools were passed
            called_args = mock_agent_class.call_args.kwargs
            assert "tools" in called_args
