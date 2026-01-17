#!/usr/bin/env python3
"""
Unit tests for the strands.py module using pytest
"""

import os
import sys
from unittest import mock

import pytest

from strands_agents_builder import strands
from strands_agents_builder.utils.session_utils import (
    handle_session_commands,
    list_sessions_command,
    setup_session_management,
)


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
        mock_agent.assert_called_with("test query")

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

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    @mock.patch.object(strands, "get_user_input")
    @mock.patch.object(strands, "Agent")
    @mock.patch.object(strands, "callback_handler")
    def test_general_exception_handling(self, mock_callback_handler, mock_agent, mock_input, mock_console_print):
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

        # Verify error was called
        mock_console_print.assert_any_call("[red]Error: Test error[/red]")

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

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    def test_shell_command_exception(
        self,
        mock_console_print,
        mock_agent,
        mock_bedrock,
        mock_load_prompt,
        mock_user_input,
        mock_welcome_message,
        monkeypatch,
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

        # Verify error was called
        mock_console_print.assert_any_call("[red]Error: Shell command failed[/red]")


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

        # Verify system prompt includes both base prompt and welcome text
        assert base_system_prompt in mock_agent.system_prompt
        assert "Custom welcome text" in mock_agent.system_prompt

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

        # Verify agent was called with system prompt that excludes welcome text reference
        assert mock_agent.system_prompt == base_system_prompt


class TestSessionManagement:
    """Test cases for session management functionality"""

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    @mock.patch("strands_agents_builder.utils.session_utils.list_available_sessions")
    def test_list_sessions_command_no_sessions(self, mock_list_sessions, mock_console_print):
        """Test list-sessions command when no sessions exist"""
        # Setup mocks
        mock_list_sessions.return_value = []

        # Mock sys.argv with session path
        with mock.patch.object(sys, "argv", ["strands", "--list-sessions", "--session-path", "/tmp/sessions"]):
            strands.main()

        # Verify appropriate message was called
        mock_console_print.assert_any_call("[yellow]No sessions found.[/yellow]")

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    @mock.patch("strands_agents_builder.utils.session_utils.get_session_info")
    @mock.patch("strands_agents_builder.utils.session_utils.list_available_sessions")
    def test_list_sessions_command_with_sessions(self, mock_list_sessions, mock_get_info, mock_console_print):
        """Test list-sessions command when sessions exist"""
        # Setup mocks
        mock_list_sessions.return_value = ["session1", "session2"]
        mock_get_info.side_effect = [
            {"session_id": "session1", "created_at": 1234567890, "total_messages": 5},
            {"session_id": "session2", "created_at": 1234567891, "total_messages": 3},
        ]

        # Mock sys.argv with session path
        with mock.patch.object(sys, "argv", ["strands", "--list-sessions", "--session-path", "/tmp/sessions"]):
            strands.main()

        # Verify sessions were listed
        mock_console_print.assert_any_call("[bold cyan]Available sessions:[/bold cyan]")
        # Check that session info was called for each session
        mock_get_info.assert_any_call("session1", "/tmp/sessions")
        mock_get_info.assert_any_call("session2", "/tmp/sessions")

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    def test_list_sessions_command_no_base_path(self, mock_console_print):
        """Test list-sessions command when no session path is configured"""
        # Mock sys.argv without session path
        with mock.patch.object(sys, "argv", ["strands", "--list-sessions"]):
            strands.main()

        # Verify appropriate error message was called
        mock_console_print.assert_called_with(
            "[red]Error: Session management not enabled. Use --session-path or "
            "set STRANDS_SESSION_PATH environment variable.[/red]"
        )

    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    def test_session_management_setup_with_path(self, mock_create_manager, mock_agent, mock_bedrock, mock_load_prompt):
        """Test session management setup when session path is provided"""
        # Setup mocks
        mock_manager = mock.MagicMock()
        mock_manager.session_id = "test-session-123"
        mock_create_manager.return_value = mock_manager

        # Mock sys.argv with session path
        with mock.patch.object(sys, "argv", ["strands", "--session-path", "/tmp/test_sessions", "test", "query"]):
            strands.main()

        # Verify session manager was created
        mock_create_manager.assert_called_once_with(None, "/tmp/test_sessions")

    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    def test_session_management_setup_with_env_var(
        self, mock_create_manager, mock_agent, mock_bedrock, mock_load_prompt
    ):
        """Test session management setup when environment variable is set"""
        # Setup mocks
        mock_manager = mock.MagicMock()
        mock_manager.session_id = "test-session-456"
        mock_create_manager.return_value = mock_manager

        # Mock environment variable and sys.argv
        with mock.patch.dict(os.environ, {"STRANDS_SESSION_PATH": "/tmp/env_sessions"}):
            with mock.patch.object(sys, "argv", ["strands", "test", "query"]):
                strands.main()

        # Verify session manager was created
        mock_create_manager.assert_called_once_with(None, "/tmp/env_sessions")

    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    def test_session_management_no_setup_when_no_path(
        self, mock_create_manager, mock_agent, mock_bedrock, mock_load_prompt
    ):
        """Test that session management is not set up when no path is provided"""
        # Mock sys.argv without session path
        with mock.patch.object(sys, "argv", ["strands", "test", "query"]):
            strands.main()

        # Verify session manager was not created
        mock_create_manager.assert_not_called()

    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    def test_agent_creation_with_session_manager(self, mock_create_manager, mock_bedrock, mock_load_prompt):
        """Test that agent is created with session manager when available"""
        # Setup mocks
        mock_manager = mock.MagicMock()
        mock_manager.session_id = "test-session-789"
        mock_create_manager.return_value = mock_manager

        with mock.patch.object(strands, "Agent") as mock_agent_class:
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            # Mock sys.argv with session path
            with mock.patch.object(sys, "argv", ["strands", "--session-path", "/tmp/test_sessions", "test", "query"]):
                strands.main()

            # Verify agent was created with session manager
            mock_agent_class.assert_called_once()
            call_kwargs = mock_agent_class.call_args[1]
            assert "session_manager" in call_kwargs
            assert call_kwargs["session_manager"] == mock_manager

    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    def test_agent_creation_without_session_manager(self, mock_create_manager, mock_bedrock, mock_load_prompt):
        """Test that agent is created without session manager when not available"""
        # Setup mocks - no session manager created
        mock_create_manager.return_value = None

        with mock.patch.object(strands, "Agent") as mock_agent_class:
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            # Mock sys.argv without session path
            with mock.patch.object(sys, "argv", ["strands", "test", "query"]):
                strands.main()

            # Verify agent was created without session manager
            mock_agent_class.assert_called_once()
            call_kwargs = mock_agent_class.call_args[1]
            assert "session_manager" not in call_kwargs or call_kwargs.get("session_manager") is None

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    @mock.patch("strands_agents_builder.utils.session_utils.get_session_info")
    def test_session_commands_in_interactive_mode(
        self,
        mock_get_info,
        mock_create_manager,
        mock_console_print,
        mock_agent,
        mock_bedrock,
        mock_load_prompt,
        mock_user_input,
        mock_welcome_message,
        mock_goodbye_message,
    ):
        """Test session-related commands in interactive mode"""
        # Setup mocks for session commands
        mock_user_input.side_effect = ["!session info", "exit"]

        # Mock session manager and info
        mock_manager = mock.MagicMock()
        mock_manager.session_id = "test-session-123"
        mock_create_manager.return_value = mock_manager
        mock_get_info.return_value = {
            "session_id": "test-session-123",
            "created_at": 1234567890,
            "total_messages": 5,
            "path": "/tmp/sessions/session_test-session-123",
        }

        # Run with session path
        with mock.patch.object(sys, "argv", ["strands", "--session-path", "/tmp/sessions"]):
            strands.main()

        # Verify session info was retrieved
        mock_get_info.assert_called_once_with("test-session-123", "/tmp/sessions")

    @mock.patch("strands_agents_builder.utils.session_utils.session_exists")
    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    def test_resume_session_command(self, mock_create_manager, mock_session_exists, mock_bedrock, mock_load_prompt):
        """Test --session-id command line argument for resuming sessions"""
        # Setup mocks
        mock_session_exists.return_value = True
        mock_manager = mock.MagicMock()
        mock_manager.session_id = "test_session"
        mock_create_manager.return_value = mock_manager

        with mock.patch.object(strands, "Agent") as mock_agent_class:
            mock_agent_instance = mock.MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            # Mock sys.argv with session ID
            with mock.patch.object(
                sys,
                "argv",
                ["strands", "--session-path", "/tmp/sessions", "--session-id", "test_session", "new", "query"],
            ):
                strands.main()

            # Verify session existence was checked
            mock_session_exists.assert_called_once_with("test_session", "/tmp/sessions")

            # Verify session manager was created with the specified ID
            mock_create_manager.assert_called_once_with("test_session", "/tmp/sessions")

            # Session resuming is now silent, no message printed

    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    def test_session_path_argument_priority(self, mock_create_manager, mock_agent, mock_bedrock, mock_load_prompt):
        """Test that --session-path argument takes priority over environment variable"""
        # Setup environment variable
        with mock.patch.dict(os.environ, {"STRANDS_SESSION_PATH": "/tmp/env_sessions"}):
            # Mock sys.argv with different session path
            with mock.patch.object(sys, "argv", ["strands", "--session-path", "/tmp/arg_sessions", "test", "query"]):
                strands.main()

            # Verify command line argument was used, not environment variable
            mock_create_manager.assert_called_once_with(None, "/tmp/arg_sessions")


class TestHelperFunctions:
    """Test cases for helper functions extracted during refactoring"""

    @mock.patch("strands_agents_builder.utils.session_utils.console.print")
    @mock.patch("strands_agents_builder.utils.session_utils.get_session_info")
    @mock.patch("strands_agents_builder.utils.session_utils.list_available_sessions")
    def test_list_sessions_command_function(self, mock_list_sessions, mock_get_info, mock_console_print):
        """Test the list_sessions_command function directly"""
        # Test with sessions available
        mock_list_sessions.return_value = ["session1", "session2"]
        mock_get_info.side_effect = [
            {"session_id": "session1", "created_at": 1234567890, "total_messages": 5},
            {"session_id": "session2", "created_at": 1234567891, "total_messages": 3},
        ]

        list_sessions_command("/tmp/sessions")

        mock_console_print.assert_any_call("[bold cyan]Available sessions:[/bold cyan]")
        # Verify get_session_info was called for each session
        mock_get_info.assert_any_call("session1", "/tmp/sessions")
        mock_get_info.assert_any_call("session2", "/tmp/sessions")

    @mock.patch("strands_agents_builder.utils.session_utils.create_session_manager")
    @mock.patch("strands_agents_builder.utils.session_utils.session_exists")
    def test_setup_session_management_function(self, mock_session_exists, mock_create_manager):
        """Test the setup_session_management function directly"""

        # Test creating new session (no session_id provided)
        mock_manager = mock.MagicMock()
        mock_manager.session_id = "generated-session-123"
        mock_create_manager.return_value = mock_manager

        result_manager, result_id, is_resuming = setup_session_management(None, "/tmp/test_sessions")

        assert result_manager == mock_manager
        assert result_id == "generated-session-123"
        assert is_resuming is False
        mock_create_manager.assert_called_with(None, "/tmp/test_sessions")

        # Test resuming existing session
        mock_session_exists.return_value = True
        mock_manager.session_id = "existing-session"

        result_manager, result_id, is_resuming = setup_session_management("existing-session", "/tmp/test_sessions")

        assert result_manager == mock_manager
        assert result_id == "existing-session"
        assert is_resuming is True

        # Test creating session with provided ID (session doesn't exist)
        mock_session_exists.return_value = False

        result_manager, result_id, is_resuming = setup_session_management("existing-session", "/tmp/test_sessions")

        assert result_manager == mock_manager
        assert result_id == "existing-session"
        assert is_resuming is False

    def test_execute_command_mode_function(self):
        """Test the execute_command_mode function directly"""
        # Create mock agent
        mock_agent = mock.MagicMock()

        # Test command execution
        strands.execute_command_mode(agent=mock_agent, query="test query", knowledge_base_id=None)

        # Verify agent was called with the query
        mock_agent.assert_called_with("test query")

    @mock.patch("builtins.print")
    @mock.patch("strands_agents_builder.utils.session_utils.get_session_info")
    def test_handle_session_commands_function(self, mock_get_info, mock_print):
        """Test the handle_session_commands function directly"""

        # Mock session info
        mock_get_info.return_value = {
            "session_id": "test-session",
            "created_at": 1234567890,
            "total_messages": 5,
            "path": "/tmp/sessions/session_test-session",
        }

        # Test session info command
        result = handle_session_commands("session info", "test-session", "/tmp/sessions")
        assert result is True
        mock_get_info.assert_called_once_with("test-session", "/tmp/sessions")

        # Test non-session command
        result = handle_session_commands("regular command", "test-session", "/tmp/sessions")
        assert result is False

    @mock.patch("builtins.print")
    def test_handle_shell_command_function(self, mock_print):
        """Test the handle_shell_command function directly"""
        # Create mock agent
        mock_agent = mock.MagicMock()

        # Test shell command handling
        strands.handle_shell_command(mock_agent, "ls -la", "!ls -la")

        # Verify shell command was executed
        mock_agent.tool.shell.assert_called_with(
            command="ls -la", user_message_override="!ls -la", non_interactive_mode=True
        )

        # Verify print was called with shell command
        mock_print.assert_called_with("$ ls -la")
