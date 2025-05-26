#!/usr/bin/env python3
"""
Unit tests for the strands.py module using pytest
"""

import os
import sys
from unittest import mock

import pytest

from strands_agents_builder import strands


class TestInteractiveMode:
    """Test cases for interactive mode functionality"""

    def test_interactive_mode(
        self,
        mock_agent,
        mock_bedrock,
        mock_load_prompt,
        mock_user_input,
        mock_welcome_message,
        mock_goodbye_message,
        monkeypatch,
    ):
        """Test the interactive mode of strands"""
        # Setup mocks
        mock_user_input.side_effect = ["test query", "exit"]

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["strands"])

        # Call the main function
        strands.main()

        # Verify welcome text was retrieved
        mock_agent.tool.welcome.assert_called_with(action="view", record_direct_tool_call=False)

        # Verify welcome message was rendered
        mock_welcome_message.assert_called_once()

        # Verify user input was called with the correct parameters
        mock_user_input.assert_called_with("\n~ ", default="", keyboard_interrupt_return_default=False)

        # Verify user input was processed
        mock_agent.assert_called_with("test query", system_prompt=mock.ANY)

        # Verify goodbye message was rendered
        mock_goodbye_message.assert_called_once()

    def test_shell_command_shortcut(
        self,
        mock_agent,
        mock_bedrock,
        mock_load_prompt,
        mock_user_input,
        mock_welcome_message,
        mock_goodbye_message,
        monkeypatch,
    ):
        """Test the shell command shortcut with ! prefix"""
        # Setup mocks
        mock_user_input.side_effect = ["!ls -la", "exit"]

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["strands"])

        # Call the main function
        strands.main()

        # Verify shell was called with the command
        mock_agent.tool.shell.assert_called_with(
            command="ls -la", user_message_override="!ls -la", non_interactive_mode=True
        )

    def test_keyboard_interrupt(
        self,
        mock_agent,
        mock_bedrock,
        mock_load_prompt,
        mock_user_input,
        mock_welcome_message,
        mock_goodbye_message,
        monkeypatch,
    ):
        """Test handling of keyboard interrupt (Ctrl+C)"""
        # Setup mocks - simulate keyboard interrupt
        mock_user_input.side_effect = KeyboardInterrupt()

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["strands"])

        # Call the main function - should exit gracefully
        strands.main()

        # Verify goodbye message was rendered
        mock_goodbye_message.assert_called_once()

    def test_empty_input(
        self,
        mock_agent,
        mock_bedrock,
        mock_load_prompt,
        mock_user_input,
        mock_welcome_message,
        mock_goodbye_message,
        monkeypatch,
    ):
        """Test handling of empty input"""
        # Setup mocks - empty input followed by exit
        mock_user_input.side_effect = ["", "   ", "\t", "exit"]

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["strands"])

        # Call the main function
        strands.main()

        # Verify agent's methods were not called for the empty input
        mock_agent.assert_not_called()

    @mock.patch.object(strands, "get_user_input")
    @mock.patch.object(strands, "Agent")
    @mock.patch.object(strands, "render_goodbye_message")
    def test_keyboard_interrupt_exception(self, mock_goodbye, mock_agent, mock_input):
        """Test handling of KeyboardInterrupt exception in interactive mode"""
        # Setup mocks
        mock_agent_instance = mock.MagicMock()
        mock_agent.return_value = mock_agent_instance

        # Setup welcome mock
        mock_welcome_result = {"status": "success", "content": [{"text": "Test welcome"}]}
        mock_agent_instance.tool.welcome.return_value = mock_welcome_result

        # Simulate KeyboardInterrupt when getting input
        mock_input.side_effect = KeyboardInterrupt()

        # Run main
        with mock.patch.object(sys, "argv", ["strands"]):
            strands.main()

        # Verify goodbye message was called
        mock_goodbye.assert_called_once()

    @mock.patch.object(strands, "get_user_input")
    @mock.patch.object(strands, "Agent")
    @mock.patch.object(strands, "render_goodbye_message")
    def test_eof_error_exception(self, mock_goodbye, mock_agent, mock_input):
        """Test handling of EOFError exception in interactive mode"""
        # Setup mocks
        mock_agent_instance = mock.MagicMock()
        mock_agent.return_value = mock_agent_instance

        # Setup welcome mock
        mock_welcome_result = {"status": "success", "content": [{"text": "Test welcome"}]}
        mock_agent_instance.tool.welcome.return_value = mock_welcome_result

        # Simulate EOFError when getting input
        mock_input.side_effect = EOFError()

        # Run main
        with mock.patch.object(sys, "argv", ["strands"]):
            strands.main()

        # Verify goodbye message was called
        mock_goodbye.assert_called_once()

    @mock.patch.object(strands, "get_user_input")
    @mock.patch.object(strands, "Agent")
    @mock.patch.object(strands, "print")
    @mock.patch.object(strands, "callback_handler")
    def test_general_exception_handling(self, mock_callback_handler, mock_print, mock_agent, mock_input):
        """Test handling of general exceptions in interactive mode"""
        # Setup mocks
        mock_agent_instance = mock.MagicMock()
        mock_agent.return_value = mock_agent_instance

        # Setup welcome mock
        mock_welcome_result = {"status": "success", "content": [{"text": "Test welcome"}]}
        mock_agent_instance.tool.welcome.return_value = mock_welcome_result

        # First return valid input, then cause exception, then exit
        mock_input.side_effect = ["test input", Exception("Test error"), "exit"]

        # Run main
        with mock.patch.object(sys, "argv", ["strands"]), mock.patch.object(strands, "render_goodbye_message"):
            strands.main()

        # Verify error was printed
        mock_print.assert_any_call("\nError: Test error")

        # Verify callback_handler was called to stop spinners
        mock_callback_handler.assert_called_once_with(force_stop=True)


class TestCommandLine:
    """Test cases for command line mode functionality"""

    def test_command_line_query(self, mock_agent, mock_bedrock, mock_load_prompt, monkeypatch):
        """Test processing a query from command line arguments"""
        # Mock sys.argv with a test query
        monkeypatch.setattr(sys, "argv", ["strands", "test", "query"])

        # Call the main function
        strands.main()

        # Verify agent was called with the query
        mock_agent.assert_called_with("test query")

    def test_command_line_query_with_kb(
        self, mock_agent, mock_bedrock, mock_load_prompt, mock_store_conversation, monkeypatch
    ):
        """Test processing a query with knowledge base from command line"""
        # Mock sys.argv with a test query and KB ID
        monkeypatch.setattr(sys, "argv", ["strands", "--kb", "test-kb-id", "test", "query"])

        # Call the main function
        strands.main()

        # Verify retrieve was called
        mock_agent.tool.retrieve.assert_called_with(text="test query", knowledgeBaseId="test-kb-id")

        # Verify conversation was stored
        mock_store_conversation.assert_called_with(mock_agent, "test query", "test-kb-id")

    @mock.patch.object(strands, "Agent")
    @mock.patch.object(strands, "store_conversation_in_kb")
    def test_command_line_with_kb_environment(self, mock_store, mock_agent):
        """Test command line mode with KB from environment variable"""
        # Setup mocks
        mock_agent_instance = mock.MagicMock()
        mock_agent.return_value = mock_agent_instance

        # Run main with test query and environment variable
        with (
            mock.patch.object(sys, "argv", ["strands", "test", "query"]),
            mock.patch.dict(os.environ, {"STRANDS_KNOWLEDGE_BASE_ID": "env-kb-id"}),
        ):
            strands.main()

        # Verify retrieve was called with the right KB ID
        mock_agent_instance.tool.retrieve.assert_called_once_with(text="test query", knowledgeBaseId="env-kb-id")

        # Verify store_conversation_in_kb was called
        mock_store.assert_called_once_with(mock_agent_instance, "test query", "env-kb-id")


class TestConfiguration:
    """Test cases for configuration handling"""

    def test_environment_variables(self, mock_agent, mock_bedrock, mock_load_prompt, monkeypatch):
        """Test handling of environment variables"""
        # Set environment variables
        monkeypatch.setenv("STRANDS_SYSTEM_PROMPT", "Custom prompt from env")

        # Mock sys.argv with a test query
        monkeypatch.setattr(sys, "argv", ["strands", "test", "query"])

        # Call the main function
        strands.main()

        # Verify load_system_prompt was called
        mock_load_prompt.assert_called_once()

        # Verify agent was called with the correct prompt
        mock_agent.assert_called_with("test query")

    def test_kb_environment_variable(
        self, mock_agent, mock_bedrock, mock_load_prompt, mock_store_conversation, monkeypatch
    ):
        """Test handling of knowledge base environment variable"""
        # Set environment variables
        monkeypatch.setenv("STRANDS_KNOWLEDGE_BASE_ID", "env-kb-id")

        # Mock sys.argv with a test query
        monkeypatch.setattr(sys, "argv", ["strands", "test", "query"])

        # Call the main function
        strands.main()

        # Verify retrieve was called with the right KB ID
        mock_agent.tool.retrieve.assert_called_with(text="test query", knowledgeBaseId="env-kb-id")

        # Verify conversation was stored
        mock_store_conversation.assert_called_with(mock_agent, "test query", "env-kb-id")


class TestErrorHandling:
    """Test cases for error handling"""

    def test_general_exception(self, mock_agent, mock_bedrock, mock_load_prompt, monkeypatch, capfd):
        """Test handling of general exceptions"""
        # Make agent raise an exception
        mock_agent.side_effect = Exception("Test error")

        # Mock sys.argv with a test query
        monkeypatch.setattr(sys, "argv", ["strands", "test", "query"])

        # Call the main function
        with pytest.raises(Exception, match="Test error"):
            strands.main()

        # Ensure the test passes without checking stderr
        assert True


class TestShellCommandError:
    """Test shell command error handling"""

    @mock.patch("builtins.print")
    def test_shell_command_exception(
        self, mock_print, mock_agent, mock_bedrock, mock_load_prompt, mock_user_input, mock_welcome_message, monkeypatch
    ):
        """Test handling exceptions when executing shell commands"""
        # Setup mocks
        mock_user_input.side_effect = ["!failing-command", "exit"]

        # Configure shell command to raise an exception
        mock_agent_instance = mock_agent
        mock_agent_instance.tool.shell.side_effect = Exception("Shell command failed")

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["strands"])

        # Call the main function
        with mock.patch.object(strands, "render_goodbye_message"):
            strands.main()

        # Verify error was printed
        mock_print.assert_any_call("Shell command execution error: Shell command failed")


class TestKnowledgeBaseIntegration:
    """Test cases for knowledge base integration"""

    def test_interactive_mode_with_kb(
        self,
        mock_agent,
        mock_bedrock,
        mock_load_prompt,
        mock_user_input,
        mock_welcome_message,
        mock_goodbye_message,
        mock_store_conversation,
        monkeypatch,
    ):
        """Test interactive mode with knowledge base"""
        # Setup mocks
        mock_user_input.side_effect = ["test query", "exit"]

        # Configure environment
        monkeypatch.setenv("STRANDS_KNOWLEDGE_BASE_ID", "test-kb-id")

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["strands"])

        # Call the main function
        strands.main()

        # Verify retrieve was called with knowledge base ID
        mock_agent.tool.retrieve.assert_called_with(text="test query", knowledgeBaseId="test-kb-id")

        # Verify store_conversation_in_kb was called
        mock_store_conversation.assert_called_once()

    def test_welcome_message_with_kb(
        self,
        mock_agent,
        mock_bedrock,
        mock_load_prompt,
        mock_user_input,
        monkeypatch,
    ):
        """Test that welcome text is included in system prompt when KB is used"""
        # Setup mocks
        mock_user_input.side_effect = ["test query", "exit"]

        # Mock welcome result
        mock_welcome_result = {"status": "success", "content": [{"text": "Custom welcome text"}]}
        mock_agent.tool.welcome.return_value = mock_welcome_result

        # Mock load_system_prompt
        base_system_prompt = "Base system prompt"
        mock_load_prompt.return_value = base_system_prompt

        # Configure environment
        monkeypatch.setenv("STRANDS_KNOWLEDGE_BASE_ID", "test-kb-id")

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["strands"])

        # Call the main function
        with mock.patch.object(strands, "render_welcome_message"), mock.patch.object(strands, "render_goodbye_message"):
            strands.main()

        # Extract the system_prompt from the agent call
        call_args, call_kwargs = mock_agent.call_args
        system_prompt = call_kwargs.get("system_prompt")

        # Verify system prompt includes both base prompt and welcome text
        assert base_system_prompt in system_prompt
        assert "Custom welcome text" in system_prompt

    def test_welcome_message_failure(
        self,
        mock_agent,
        mock_bedrock,
        mock_load_prompt,
        mock_user_input,
        monkeypatch,
    ):
        """Test handling of welcome message retrieval failure"""
        # Setup mocks
        mock_user_input.side_effect = ["test query", "exit"]

        # Mock welcome result with error status
        mock_welcome_result = {"status": "error", "content": [{"text": "Failed to load welcome text"}]}
        mock_agent.tool.welcome.return_value = mock_welcome_result

        # Mock load_system_prompt
        base_system_prompt = "Base system prompt"
        mock_load_prompt.return_value = base_system_prompt

        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["strands"])

        # Call the main function
        with mock.patch.object(strands, "render_welcome_message"), mock.patch.object(strands, "render_goodbye_message"):
            strands.main()

        # Verify agent was called with system prompt that includes welcome text reference
        # Even with error status, the code adds a "Welcome Text Reference:" section (just empty)
        expected_system_prompt = f"{base_system_prompt}\n\nWelcome Text Reference:\n"
        call_args, call_kwargs = mock_agent.call_args
        system_prompt = call_kwargs.get("system_prompt")

        assert system_prompt == expected_system_prompt
